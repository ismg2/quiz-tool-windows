# Quiz Tool - Application Windows Standalone

Application de quiz entièrement autonome pour Windows. **Aucune installation requise.**

---

## Télécharger l'Application

### Méthode 1 : GitHub Actions (Recommandé)

1. Allez dans l'onglet **Actions** sur GitHub
2. Cliquez sur le dernier workflow **"Build Windows EXE"** réussi (✓ vert)
3. En bas de la page, téléchargez **QuizTool-Windows-Distribution**
4. Extrayez le ZIP

### Méthode 2 : Compiler vous-même

Voir la section [Développeurs](#pour-les-développeurs) en bas.

---

## Utilisation

### Contenu du ZIP

```
QuizTool-Distribution/
├── QuizTool.exe      ← Double-cliquez pour lancer
├── quizzes/          ← Vos fichiers de quiz
│   ├── stm32-mcu.json
│   ├── edge-ai.json
│   └── pipeline-b2b.json
└── LISEZ-MOI.txt
```

### Lancer un Quiz

1. **Double-cliquez** sur `QuizTool.exe`
2. Une fenêtre console noire s'ouvre
3. Le **navigateur s'ouvre automatiquement** sur la page de sélection
4. Choisissez un quiz, entrez votre nom, commencez !

### Arrêter l'Application

Fermez la fenêtre noire (console).

---

## Ajouter / Modifier des Quiz

Placez vos fichiers `.json` dans le dossier `quizzes/` à côté de l'exe.

### Format d'un Fichier Quiz

```json
{
  "quiz_title": "Mon Quiz",
  "description": "Description affichée sur la page de démarrage",
  "time_per_question": 45,
  "questions": [
    {
      "id": 1,
      "type": "single",
      "question": "Quelle est la capitale de la France ?",
      "options": ["Lyon", "Paris", "Marseille", "Bordeaux"],
      "correct": [1],
      "explanation": "Paris est la capitale de la France."
    },
    {
      "id": 2,
      "type": "multiple",
      "question": "Sélectionnez les nombres pairs :",
      "options": ["1", "2", "3", "4"],
      "correct": [1, 3],
      "explanation": "2 et 4 sont des nombres pairs (indices 1 et 3)."
    }
  ]
}
```

### Champs

| Champ | Description |
|-------|-------------|
| `type` | `"single"` = une seule réponse, `"multiple"` = plusieurs réponses |
| `correct` | Tableau des **indices** des bonnes réponses (commence à 0) |
| `time_per_question` | Secondes par question (optionnel, défaut: 60) |

---

## Fonctionnalités

- Interface web moderne et responsive
- Support multi-quiz (plusieurs fichiers JSON)
- Timer configurable par question
- Mélange automatique des questions et options
- Résultats chiffrés (token sécurisé)
- Décodeur de résultats intégré
- Détection anti-triche (changement d'onglet, perte de focus)
- **100% hors-ligne** - aucune connexion internet requise

---

## Décoder les Résultats

À la fin du quiz, le participant reçoit un **token chiffré** (code long).

### Pour le Déchiffrer

1. Ouvrez `http://127.0.0.1:5050/decode`
2. Collez le token du participant
3. Entrez la clé secrète
4. Visualisez le score détaillé et le rapport anti-triche

**Clé par défaut :** `your-secret-key-change-me`

---

## Pour les Développeurs

### Compiler sur Windows

Nécessite : Windows + Python 3.8+

```batch
pip install flask cryptography waitress pyinstaller
pyinstaller --clean --noconfirm quiz_tool.spec
```

L'exe sera dans `dist/QuizTool.exe`.

### Modifier la Clé de Chiffrement

Éditez `app_standalone.py`, ligne 36 :

```python
RESULT_ENCRYPTION_KEY = 'votre-nouvelle-cle-secrete'
```

Recompilez ensuite l'exe.

### Structure du Projet

```
quiz-tool-windows/
├── app_standalone.py     # Application Flask principale
├── quiz_tool.spec        # Configuration PyInstaller
├── requirements.txt      # Dépendances Python
├── templates/            # Pages HTML (Jinja2)
├── static/               # CSS et JavaScript
├── quizzes/              # Fichiers quiz JSON
└── .github/workflows/    # Build automatique GitHub Actions
```

---

## Dépannage

### L'exe ne se lance pas

- Windows peut bloquer les exe téléchargés : clic droit → Propriétés → Débloquer
- Antivirus peut bloquer : ajoutez une exception

### Port 5050 déjà utilisé

Modifiez dans `app_standalone.py` :
```python
PORT = 5051  # Choisir un autre port
```

### Le navigateur ne s'ouvre pas

Ouvrez manuellement : `http://127.0.0.1:5050`

---

## Sécurité

- Résultats chiffrés avec Fernet (AES-128)
- Réponses correctes jamais envoyées au navigateur
- Validation côté serveur uniquement
- Violations anti-triche enregistrées mais n'empêchent pas de terminer
