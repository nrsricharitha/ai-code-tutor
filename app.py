# FULL UPDATED app.py


from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import re
from pathlib import Path

app = Flask(__name__)
app.secret_key = "super-secret-key"

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "ai_code_tutor.db"

SUPPORTED_LANGUAGES = [
    "English",
    "Telugu",
    "Hindi",
    "Tamil",
    "Kannada",
    "Marathi"
]

TRANSLATIONS = {
    "loop": {
        "English": "This loop repeats instructions multiple times.",
        "Telugu": "ఈ లూప్ ఒకే సూచనలను మళ్లీ మళ్లీ అమలు చేస్తుంది.",
        "Hindi": "यह लूप निर्देशों को बार-बार चलाता है.",
        "Tamil": "இந்த லூப் வழிமுறைகளை மீண்டும் மீண்டும் இயக்குகிறது.",
        "Kannada": "ಈ ಲೂಪ್ ಸೂಚನೆಗಳನ್ನು ಪುನರಾವರ್ತಿಸುತ್ತದೆ.",
        "Marathi": "हा लूप सूचना पुन्हा पुन्हा चालवतो."
    },

    "condition": {
        "English": "This condition checks if something is true or false.",
        "Telugu": "ఈ కండిషన్ నిజమా కాదా అని పరీక్షిస్తుంది.",
        "Hindi": "यह कंडीशन सही या गलत जांचती है.",
        "Tamil": "இந்த நிபந்தனை உண்மையா பொய்யா என பார்க்கிறது.",
        "Kannada": "ಈ ಷರತ್ತು ಸತ್ಯವೋ ಅಸತ್ಯವೋ ಪರಿಶೀಲಿಸುತ್ತದೆ.",
        "Marathi": "ही अट खरी की खोटी तपासते."
    },

    "output": {
        "English": "This line displays output.",
        "Telugu": "ఈ లైన్ ఫలితాన్ని చూపిస్తుంది.",
        "Hindi": "यह लाइन आउटपुट दिखाती है.",
        "Tamil": "இந்த வரி வெளியீட்டை காட்டுகிறது.",
        "Kannada": "ಈ ಸಾಲು ಔಟ್‌ಪುಟ್ ತೋರಿಸುತ್ತದೆ.",
        "Marathi": "ही ओळ आउटपुट दाखवते."
    },

    "variable": {
        "English": "This line stores a value inside a variable.",
        "Telugu": "ఈ లైన్ ఒక విలువను వేరియబుల్‌లో నిల్వ చేస్తుంది.",
        "Hindi": "यह लाइन वैरिएबल में वैल्यू स्टोर करती है.",
        "Tamil": "இந்த வரி ஒரு மதிப்பை மாறியில் சேமிக்கிறது.",
        "Kannada": "ಈ ಸಾಲು ಮೌಲ್ಯವನ್ನು ವ್ಯೇರಿಯಬಲ್‌ನಲ್ಲಿ ಸಂಗ್ರಹಿಸುತ್ತದೆ.",
        "Marathi": "ही ओळ व्हेरिएबलमध्ये मूल्य साठवते."
    },

    "general": {
        "English": "This line performs an operation.",
        "Telugu": "ఈ లైన్ ఒక ఆపరేషన్‌ను నిర్వహిస్తుంది.",
        "Hindi": "यह लाइन एक कार्य करती है.",
        "Tamil": "இந்த வரி ஒரு செயல்பாட்டை செய்கிறது.",
        "Kannada": "ಈ ಸಾಲು ಒಂದು ಕಾರ್ಯವನ್ನು ನಿರ್ವಹಿಸುತ್ತದೆ.",
        "Marathi": "ही ओळ एक कार्य करते."
    }
}

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
        '''
    )

    conn.commit()
    conn.close()

def classify_line(line):
    stripped = line.strip()

    if re.search(r"\bfor\b|\bwhile\b", stripped):
        return "loop"

    if re.search(r"\bif\b|\belse\b", stripped):
        return "condition"

    if re.search(r"print|console.log|printf|cout", stripped):
        return "output"

    if "=" in stripped:
        return "variable"

    return "general"

def explain_code_lines(code, language):
    lines = []

    for index, line in enumerate(code.splitlines(), start=1):
        line_type = classify_line(line)

        explanation = TRANSLATIONS.get(
            line_type,
            TRANSLATIONS["general"]
        ).get(language)

        lines.append({
            "number": index,
            "code": line,
            "explanation": explanation
        })

    return lines

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, password)
            )

            conn.commit()

        except:
            return render_template(
                "signup.html",
                error="Email already exists"
            )

        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["name"] = user["name"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password"
        )

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["name"],
        languages=SUPPORTED_LANGUAGES
    )

@app.route("/api/explain", methods=["POST"])
def explain():

    data = request.get_json()

    code = data.get("code", "")
    language = data.get("language", "English")

    lines = explain_code_lines(code, language)

    return jsonify({
        "lines": lines
    })

init_db()

if __name__ == "__main__":
    app.run(debug=True)
```
