/**
 * Quiz Tool - Anti-cheat and quiz functionality
 * Single-page version - no page reloads during quiz
 */

// State
let timeRemaining = TIME_LIMIT;
let timerInterval = null;
let violationCount = 0;
let isFullscreen = false;
let hasStarted = false;

// DOM Elements
const quizContainer = document.getElementById('quiz-container');
const fullscreenWarning = document.getElementById('fullscreen-warning');
const tabWarning = document.getElementById('tab-warning');
const timerElement = document.getElementById('timer');
const timeDisplay = document.getElementById('time-remaining');
const violationDisplay = document.getElementById('violation-count');
const nextBtn = document.getElementById('next-btn');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const questionText = document.getElementById('question-text');
const optionsContainer = document.getElementById('options-container');
const questionTypeBadge = document.getElementById('question-type-badge');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    document.body.classList.add('quiz-active');
    setupAntiCheat();
    setupOptionListeners();
    checkFullscreen();
});

// Setup click listeners for options
function setupOptionListeners() {
    const options = document.querySelectorAll('.option');
    options.forEach(option => {
        option.addEventListener('click', function() {
            const input = this.querySelector('input');
            const isMultiple = input.type === 'checkbox';

            if (isMultiple) {
                this.classList.toggle('selected');
                input.checked = this.classList.contains('selected');
            } else {
                // Single choice - deselect others
                document.querySelectorAll('.option').forEach(opt => {
                    opt.classList.remove('selected');
                    opt.querySelector('input').checked = false;
                });
                this.classList.add('selected');
                input.checked = true;
            }
        });
    });
}

// Anti-cheat setup
function setupAntiCheat() {
    // Disable right-click
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        reportCheat('focus_losses');
        return false;
    });

    // Disable certain keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Disable F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U
        if (
            e.key === 'F12' ||
            (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i')) ||
            (e.ctrlKey && e.shiftKey && (e.key === 'J' || e.key === 'j')) ||
            (e.ctrlKey && (e.key === 'U' || e.key === 'u'))
        ) {
            e.preventDefault();
            reportCheat('focus_losses');
            return false;
        }
    });

    // Detect tab/window visibility changes
    document.addEventListener('visibilitychange', function() {
        if (document.hidden && hasStarted) {
            handleTabSwitch();
        }
    });

    // Detect window blur (switching to another app)
    window.addEventListener('blur', function() {
        if (hasStarted) {
            handleTabSwitch();
        }
    });

    // Detect fullscreen changes
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    // Detect dev tools (basic detection via window resize)
    let devToolsOpen = false;
    const threshold = 160;
    setInterval(function() {
        const widthThreshold = window.outerWidth - window.innerWidth > threshold;
        const heightThreshold = window.outerHeight - window.innerHeight > threshold;

        if ((widthThreshold || heightThreshold) && !devToolsOpen) {
            devToolsOpen = true;
            reportCheat('focus_losses');
        } else if (!(widthThreshold || heightThreshold)) {
            devToolsOpen = false;
        }
    }, 1000);
}

// Fullscreen functions
function checkFullscreen() {
    isFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
    );

    if (!isFullscreen) {
        showFullscreenWarning();
    } else {
        hideFullscreenWarning();
        startQuiz();
    }
}

function enterFullscreen() {
    const elem = document.documentElement;

    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.mozRequestFullScreen) {
        elem.mozRequestFullScreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
}

function handleFullscreenChange() {
    const wasFullscreen = isFullscreen;
    isFullscreen = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
    );

    if (wasFullscreen && !isFullscreen && hasStarted) {
        reportCheat('fullscreen_exits');
        showFullscreenWarning();
    } else if (isFullscreen) {
        hideFullscreenWarning();
        if (!hasStarted) {
            startQuiz();
        }
    }
}

function showFullscreenWarning() {
    fullscreenWarning.classList.remove('hidden');
}

function hideFullscreenWarning() {
    fullscreenWarning.classList.add('hidden');
}

function startQuiz() {
    if (!hasStarted) {
        hasStarted = true;
        if (TIME_LIMIT > 0) {
            startTimer();
        }
    }
}

// Timer functions
function startTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    timeRemaining = TIME_LIMIT;
    updateTimerDisplay();

    timerInterval = setInterval(function() {
        timeRemaining--;
        updateTimerDisplay();

        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            autoSubmit();
        }
    }, 1000);
}

function updateTimerDisplay() {
    if (timeDisplay) {
        timeDisplay.textContent = timeRemaining;

        if (timerElement) {
            timerElement.classList.remove('warning', 'danger');

            if (timeRemaining <= 10) {
                timerElement.classList.add('danger');
            } else if (timeRemaining <= 20) {
                timerElement.classList.add('warning');
            }
        }
    }
}

// Tab switch handling
function handleTabSwitch() {
    violationCount++;
    reportCheat('tab_switches');
    showTabWarning();
}

function showTabWarning() {
    if (violationDisplay) {
        violationDisplay.textContent = violationCount;
    }
    tabWarning.classList.remove('hidden');
}

function dismissWarning() {
    tabWarning.classList.add('hidden');

    // Re-enter fullscreen if needed
    if (!isFullscreen) {
        enterFullscreen();
    }
}

// Cheat reporting
function reportCheat(type) {
    fetch('/api/cheat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type: type })
    }).catch(err => console.error('Failed to report:', err));
}

// Answer submission
function getSelectedAnswers() {
    const inputs = optionsContainer.querySelectorAll('input:checked');
    return Array.from(inputs).map(input => parseInt(input.value));
}

function submitAnswer() {
    const answers = getSelectedAnswers();

    return fetch('/api/answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answer: answers })
    });
}

// Render new question without page reload
function renderQuestion(data) {
    // Update progress
    currentQuestionNum = data.question_num;
    totalQuestions = data.total_questions;
    isLastQuestion = data.is_last;
    questionType = data.question.type;

    const progress = (currentQuestionNum / totalQuestions) * 100;
    progressFill.style.width = progress + '%';
    progressText.textContent = `Question ${currentQuestionNum} of ${totalQuestions}`;

    // Update question type badge
    if (data.question.type === 'multiple') {
        questionTypeBadge.textContent = 'Select all that apply';
        questionTypeBadge.className = 'badge badge-info';
    } else {
        questionTypeBadge.textContent = 'Select one answer';
        questionTypeBadge.className = 'badge';
    }

    // Update question text
    questionText.textContent = data.question.question;

    // Update options
    const inputType = data.question.type === 'multiple' ? 'checkbox' : 'radio';
    let optionsHTML = '';
    data.question.options.forEach((option, index) => {
        optionsHTML += `
            <label class="option" data-index="${index}">
                <input type="${inputType}" name="answer" value="${index}">
                <span class="option-text">${option}</span>
            </label>
        `;
    });
    optionsContainer.innerHTML = optionsHTML;

    // Re-attach click listeners
    setupOptionListeners();

    // Update button text
    nextBtn.textContent = isLastQuestion ? 'Finish Quiz' : 'Next Question';
    nextBtn.disabled = false;

    // Reset and start timer
    if (TIME_LIMIT > 0) {
        startTimer();
    }
}

function submitAndNext() {
    // Disable button to prevent double-clicks
    nextBtn.disabled = true;
    nextBtn.textContent = 'Loading...';

    // Clear timer
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    // Submit answer then get next question
    submitAnswer()
        .then(() => fetch('/api/next', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }))
        .then(response => response.json())
        .then(data => {
            if (data.finished) {
                // Quiz is done, go to submit page
                window.location.href = data.redirect;
            } else {
                // Render next question without page reload
                renderQuestion(data);
            }
        })
        .catch(err => {
            console.error('Error:', err);
            nextBtn.disabled = false;
            nextBtn.textContent = isLastQuestion ? 'Finish Quiz' : 'Next Question';
        });
}

function autoSubmit() {
    // Time's up - auto submit current answer and move on
    submitAndNext();
}

// Prevent print screen (basic)
document.addEventListener('keyup', function(e) {
    if (e.key === 'PrintScreen') {
        reportCheat('focus_losses');
    }
});

// Console warning
console.log('%cStop!', 'color: red; font-size: 50px; font-weight: bold;');
console.log('%cThis is a browser feature intended for developers.', 'font-size: 18px;');
console.log('%cUsing developer tools during the quiz will be recorded as a violation.', 'font-size: 18px; color: orange;');
