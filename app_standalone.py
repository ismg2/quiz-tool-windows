#!/usr/bin/env python3
"""
Quiz Tool - Standalone Windows Application
Multi-quiz support, auto-opens browser
"""

import json
import random
import base64
import hashlib
import sys
import os
import uuid
import webbrowser
import threading
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from cryptography.fernet import Fernet, InvalidToken

# Determine if running as exe or script
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    DATA_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = BASE_DIR

# Flask app with correct paths for exe
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'quiz-tool-secret-key-2024'
    RESULT_ENCRYPTION_KEY = os.environ.get('RESULT_KEY') or 'your-secret-key-change-me'
    SHUFFLE_QUESTIONS = True
    SHUFFLE_OPTIONS = True
    TIME_PER_QUESTION = 60

app.config.from_object(Config)

# Quizzes folder - check DATA_DIR first (next to exe), then BASE_DIR (bundled)
def get_quizzes_folder():
    data_quizzes = os.path.join(DATA_DIR, 'quizzes')
    if os.path.exists(data_quizzes):
        return data_quizzes
    return os.path.join(BASE_DIR, 'quizzes')

def get_available_quizzes():
    """List all available quiz files."""
    quizzes = []
    quizzes_folder = get_quizzes_folder()
    if os.path.exists(quizzes_folder):
        for filename in os.listdir(quizzes_folder):
            if filename.endswith('.json'):
                filepath = os.path.join(quizzes_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        quizzes.append({
                            'id': filename[:-5],
                            'filename': filename,
                            'title': data.get('quiz_title', filename),
                            'description': data.get('description', ''),
                            'question_count': len(data.get('questions', []))
                        })
                except:
                    pass
    return quizzes

def load_questions(quiz_id=None):
    """Load questions from a specific quiz file."""
    quizzes_folder = get_quizzes_folder()
    if quiz_id:
        filepath = os.path.join(quizzes_folder, f'{quiz_id}.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    # Fallback
    fallback = os.path.join(DATA_DIR, 'questions.json')
    if not os.path.exists(fallback):
        fallback = os.path.join(BASE_DIR, 'questions.json')
    if os.path.exists(fallback):
        with open(fallback, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'quiz_title': 'Quiz', 'questions': []}

def get_encryption_key():
    key = Config.RESULT_ENCRYPTION_KEY.encode()
    hashed = hashlib.sha256(key).digest()
    return base64.urlsafe_b64encode(hashed)

def encrypt_result(data):
    f = Fernet(get_encryption_key())
    json_data = json.dumps(data).encode()
    return f.encrypt(json_data).decode()

def decrypt_result(token):
    f = Fernet(get_encryption_key())
    decrypted = f.decrypt(token.encode())
    return json.loads(decrypted.decode())

# Server-side storage for quiz data that exceeds cookie size limits (~4KB).
# Flask's default cookie-based sessions can't hold full quiz question sets.
_server_sessions = {}

def _get_server_data():
    """Get server-side data for the current session."""
    sid = session.get('_sid')
    if sid and sid in _server_sessions:
        return _server_sessions[sid]
    return {}

def _set_server_data(key, value):
    """Store data server-side for the current session."""
    sid = session.get('_sid')
    if not sid:
        sid = str(uuid.uuid4())
        session['_sid'] = sid
    if sid not in _server_sessions:
        _server_sessions[sid] = {}
    _server_sessions[sid][key] = value

def _clear_server_data():
    """Clear server-side data for the current session."""
    sid = session.get('_sid')
    if sid and sid in _server_sessions:
        del _server_sessions[sid]

def quiz_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'quiz_started' not in session or not session['quiz_started']:
            flash('Please start the quiz first.', 'warning')
            return redirect(url_for('index'))
        if session.get('quiz_completed'):
            return redirect(url_for('result'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Quiz selection page."""
    _clear_server_data()
    session.clear()
    quizzes = get_available_quizzes()
    return render_template('select_quiz.html', quizzes=quizzes)

@app.route('/quiz/<quiz_id>')
def select_quiz(quiz_id):
    """Start page for a specific quiz."""
    # Clear quiz-related data
    _clear_server_data()
    for key in ['quiz_started', 'quiz_completed', 'answers',
                'current_question', 'score', 'total']:
        session.pop(key, None)
    session['selected_quiz'] = quiz_id
    quiz_data = load_questions(quiz_id)
    if not quiz_data.get('questions'):
        flash('Quiz not found or empty.', 'error')
        return redirect(url_for('index'))
    return render_template('start.html',
                         quiz_id=quiz_id,
                         quiz_title=quiz_data.get('quiz_title', 'Quiz'),
                         description=quiz_data.get('description', ''))

@app.route('/start', methods=['POST'])
def start_quiz():
    participant_name = request.form.get('name', '').strip()
    quiz_id = request.form.get('quiz_id') or session.get('selected_quiz')

    # Validate quiz_id exists
    if not quiz_id:
        flash('No quiz selected. Please select a quiz.', 'error')
        return redirect(url_for('index'))

    if not participant_name:
        flash('Please enter your name.', 'error')
        return redirect(url_for('select_quiz', quiz_id=quiz_id))

    session['selected_quiz'] = quiz_id
    quiz_data = load_questions(quiz_id)

    # Validate quiz has questions
    if not quiz_data.get('questions'):
        flash('Quiz not found or has no questions.', 'error')
        return redirect(url_for('index'))
    questions = quiz_data['questions'].copy()

    if Config.SHUFFLE_QUESTIONS:
        random.shuffle(questions)

    prepared_questions = []
    for q in questions:
        options = list(enumerate(q['options']))
        if Config.SHUFFLE_OPTIONS:
            random.shuffle(options)
        original_to_shuffled = {orig_idx: new_idx for new_idx, (orig_idx, _) in enumerate(options)}
        prepared_questions.append({
            'id': q['id'],
            'type': q['type'],
            'question': q['question'],
            'options': [opt for _, opt in options],
            'option_map': original_to_shuffled,
            'correct': q['correct'],
            'explanation': q.get('explanation', '')
        })

    # Store large quiz data server-side (exceeds cookie ~4KB limit)
    _set_server_data('questions', prepared_questions)

    session['quiz_started'] = True
    session['quiz_completed'] = False
    session['participant_name'] = participant_name
    session['current_question'] = 0
    session['answers'] = {}
    session['start_time'] = datetime.now().isoformat()
    session['question_times'] = {}
    session['cheat_flags'] = {'tab_switches': 0, 'fullscreen_exits': 0, 'focus_losses': 0}
    session['time_per_question'] = quiz_data.get('time_per_question', Config.TIME_PER_QUESTION)

    return redirect(url_for('quiz'))

@app.route('/quiz')
@quiz_required
def quiz():
    current_idx = session.get('current_question', 0)
    questions = _get_server_data().get('questions', [])
    if current_idx >= len(questions):
        return redirect(url_for('submit'))
    question = questions[current_idx]
    return render_template('quiz.html',
                         question=question,
                         question_num=current_idx + 1,
                         total_questions=len(questions),
                         time_per_question=session.get('time_per_question', 60),
                         existing_answer=session['answers'].get(str(current_idx)))

@app.route('/api/answer', methods=['POST'])
@quiz_required
def submit_answer():
    data = request.get_json()
    current_idx = session.get('current_question', 0)
    answer = data.get('answer', [])
    if not isinstance(answer, list):
        answer = [answer]
    session['answers'][str(current_idx)] = answer
    session['question_times'][str(current_idx)] = datetime.now().isoformat()
    session.modified = True
    return jsonify({'success': True})

@app.route('/api/next', methods=['POST'])
@quiz_required
def next_question():
    current_idx = session.get('current_question', 0)
    questions = _get_server_data().get('questions', [])
    if current_idx < len(questions) - 1:
        session['current_question'] = current_idx + 1
        session.modified = True
        next_q = questions[current_idx + 1]
        return jsonify({
            'success': True, 'finished': False,
            'question': {'type': next_q['type'], 'question': next_q['question'], 'options': next_q['options']},
            'question_num': current_idx + 2,
            'total_questions': len(questions),
            'is_last': (current_idx + 2) == len(questions)
        })
    return jsonify({'success': True, 'finished': True, 'redirect': url_for('submit')})

@app.route('/api/cheat', methods=['POST'])
@quiz_required
def report_cheat():
    data = request.get_json()
    cheat_type = data.get('type')
    if cheat_type in session['cheat_flags']:
        session['cheat_flags'][cheat_type] += 1
        session.modified = True
    return jsonify({'success': True})

@app.route('/submit', methods=['GET', 'POST'])
@quiz_required
def submit():
    if request.method == 'GET':
        return render_template('submit_confirm.html',
                             answered=len(session.get('answers', {})),
                             total=len(_get_server_data().get('questions', [])))
    try:
        questions = _get_server_data().get('questions', [])
        answers = session.get('answers', {})
        results = []
        review_results = []
        correct_count = 0

        for idx, question in enumerate(questions):
            user_answer = answers.get(str(idx), [])
            user_answer = [int(a) for a in user_answer] if user_answer else []
            option_map = {int(k): int(v) for k, v in question['option_map'].items()}
            reverse_map = {v: k for k, v in option_map.items()}
            original_user_answer = sorted([reverse_map.get(a, a) for a in user_answer])
            correct_answer = sorted([int(c) for c in question['correct']])
            is_correct = original_user_answer == correct_answer
            if is_correct:
                correct_count += 1

            results.append({
                'question_id': question['id'], 'question': question['question'],
                'user_answer': original_user_answer, 'correct_answer': correct_answer,
                'is_correct': is_correct, 'explanation': question['explanation']
            })
            correct_shuffled = [option_map.get(int(c), c) for c in question['correct']]
            review_results.append({
                'question_id': question['id'], 'question': question['question'],
                'options': question['options'], 'user_answer': user_answer,
                'correct_answer': correct_shuffled, 'is_correct': is_correct,
                'explanation': question['explanation']
            })

        quiz_id = session.get('selected_quiz')
        result_data = {
            'participant': session['participant_name'],
            'quiz_title': load_questions(quiz_id).get('quiz_title', 'Quiz'),
            'start_time': session['start_time'],
            'end_time': datetime.now().isoformat(),
            'score': correct_count,
            'total': len(questions),
            'percentage': round(correct_count / len(questions) * 100, 1) if questions else 0,
            'results': results,
            'cheat_flags': session['cheat_flags'],
            'question_times': session['question_times']
        }

        token = encrypt_result(result_data)
        # Store large data server-side
        _set_server_data('review_results', review_results)
        _set_server_data('result_token', token)

        session['quiz_completed'] = True
        session['score'] = correct_count
        session['total'] = len(questions)
        session.modified = True
        return redirect(url_for('review', q=1))

    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/review')
def review():
    if not session.get('quiz_completed'):
        flash('Please complete the quiz first.', 'warning')
        return redirect(url_for('index'))
    review_results = _get_server_data().get('review_results', [])
    total = len(review_results)
    q = request.args.get('q', 1, type=int)
    q = max(1, min(q, total))
    item = review_results[q - 1]
    return render_template('review.html', item=item, options=item['options'],
                         question_num=q, total=total, results=review_results,
                         score=session.get('score', 0))

@app.route('/result')
def result():
    if not session.get('quiz_completed'):
        flash('Please complete the quiz first.', 'warning')
        return redirect(url_for('index'))
    return render_template('result.html',
                         token=_get_server_data().get('result_token', ''),
                         score=session.get('score', 0),
                         total=session.get('total', 0),
                         participant=session.get('participant_name', ''))

@app.route('/decode', methods=['GET', 'POST'])
def decode():
    result_data = None
    error = None
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        secret_key = request.form.get('secret_key', '').strip()
        if not token:
            error = 'Please enter a result token.'
        elif not secret_key:
            error = 'Please enter the secret key.'
        elif secret_key != Config.RESULT_ENCRYPTION_KEY:
            error = 'Invalid secret key.'
        else:
            try:
                result_data = decrypt_result(token)
            except InvalidToken:
                error = 'Invalid or corrupted token.'
            except Exception as e:
                error = f'Error: {str(e)}'
    return render_template('decode.html', result=result_data, error=error)

def open_browser(port):
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://127.0.0.1:{port}')

if __name__ == '__main__':
    PORT = 5050
    threading.Thread(target=open_browser, args=(PORT,), daemon=True).start()
    print(f"\n{'='*50}")
    print("Quiz Tool - Running")
    print(f"{'='*50}")
    print(f"\nURL: http://127.0.0.1:{PORT}")
    print(f"Decode: http://127.0.0.1:{PORT}/decode")
    print(f"Secret Key: {Config.RESULT_ENCRYPTION_KEY}")
    print(f"\nClose this window to stop.")
    print(f"{'='*50}\n")

    try:
        from waitress import serve
        serve(app, host='127.0.0.1', port=PORT, threads=4)
    except ImportError:
        app.run(host='127.0.0.1', port=PORT, debug=False, threaded=True)
