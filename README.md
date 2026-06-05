# AI Code Tutor

AI Code Tutor is a full-stack educational web application for beginner programmers. It explains code in English, Telugu, Hindi, Marathi, Kannada, Tamil, or all languages together using AI-like rule-based logic.

## Features

- Animated welcome page
- Sign up, login, logout, and Flask session management
- Functional local forgot/reset password flow
- SQLite user database
- Skill level and language preference setup
- Dashboard with code editor, examples, dark/light mode, and sidebar
- Voice input with browser SpeechRecognition
- Voice output with browser SpeechSynthesis
- Automatic language detection for C, C++, Python, and JavaScript
- Line-by-line explanations
- Detection for variables, loops, functions, conditions, input/output, and arrays
- Beginner-friendly error suggestions
- English, Telugu, Hindi, Marathi, Kannada, Tamil, and Multiple Languages explanation modes

## Folder Structure

```text
AI Code Tutor/
├── app.py
├── requirements.txt
├── README.md
├── ai_code_tutor.db        # Created automatically when the app runs
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── setup.html
│   ├── dashboard.html
│   ├── forgot_password.html
│   └── reset_password.html
└── static/
    ├── style.css
    ├── script.js
    └── animations.css
```

## Installation

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

```bash
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
python app.py
```

Open this URL in your browser:

```text
http://127.0.0.1:5000
```

## Example Screenshots Description

- Welcome screen: Gradient EdTech hero page with animated glass cards and a Get Started button.
- Auth screens: Clean centered glass forms for sign up and login.
- Setup screen: Skill level and language preference cards.
- Dashboard: Sidebar navigation, large code input area, action buttons, theme toggle, and explanation cards.

## Notes

This project uses rule-based AI-like logic, so it runs locally without needing an external AI API key.
