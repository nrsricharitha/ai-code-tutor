# AI Code Tutor

AI Code Tutor is a Flask, SQLite, HTML, CSS, and JavaScript web application that explains programming code in beginner-friendly multilingual language.

## Features

- Modern landing page
- Signup, login, logout, forgot password, and reset password
- SQLite user storage with hashed passwords
- User setup for skill level and preferred language
- Dashboard code editor
- Dark/light mode toggle
- Line-by-line code explanations
- Support for Python, C, C++, Java, and JavaScript
- Multilingual explanations: English, Telugu, Hindi, Marathi, Kannada, and Tamil
- Syntax mistake detection with fix suggestions
- Programming concept detection
- Code complexity meter
- Expected output prediction
- Learning roadmap
- Quiz generator
- Progress tracker
- Analysis history
- Saved/favorite explanations
- Download as PDF using browser print
- Render-ready with Gunicorn

## Folder Structure

```text
project/
├── app.py
├── requirements.txt
├── README.md
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

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Render Settings

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```
