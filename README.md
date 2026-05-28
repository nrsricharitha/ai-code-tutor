# AI Code Tutor

AI Code Tutor is a full-stack educational web application for beginner programmers. It explains code in English, Telugu, Hindi, Marathi, Kannada, Tamil, or all languages together using AI-like rule-based logic.

## Features

- Animated welcome page
- Sign up, login, logout, and Flask session management
- SQLite user database
- Skill level and language preference setup
- Dashboard with code editor, examples, dark/light mode, and sidebar
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
│   └── dashboard.html
└── static/
    ├── style.css
    └── script.js

- Setup screen: Skill level and language preference cards.
- Dashboard: Sidebar navigation, large code input area, action buttons, theme toggle, and explanation cards.

## Notes

This project uses rule-based AI-like logic, so it runs locally without needing an external AI API key.
