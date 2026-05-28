from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import re
import sqlite3
from pathlib import Path


# Basic Flask setup. The secret key protects login sessions in the browser.
app = Flask(__name__)
app.secret_key = "replace-this-secret-key-for-production"

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "ai_code_tutor.db"

SUPPORTED_LANGUAGES = ["English", "Telugu", "Hindi", "Marathi", "Kannada", "Tamil"]

TRANSLATED_PHRASES = {
    "Telugu": {
        "blank": "ఈ ఖాళీ లైన్ కోడ్‌ను చదవడానికి సులభంగా చేస్తుంది.",
        "comment": "ఇది కామెంట్. ఇది మనుషుల కోసం వివరణ ఇస్తుంది, కంప్యూటర్ దాన్ని అమలు చేయదు.",
        "variable": "వేరియబుల్ డేటాను నిల్వ చేసే చిన్న పెట్టెలా పనిచేస్తుంది.",
        "loop": "లూప్ ఒకే పనిని మళ్లీ మళ్లీ చేయడానికి ఉపయోగపడుతుంది.",
        "condition": "కండిషన్ నిజమా కాదా అని చూసి నిర్ణయం తీసుకుంటుంది.",
        "function": "ఫంక్షన్ ఒక పని కోసం తయారు చేసిన చిన్న యంత్రంలాంటిది.",
        "input": "ఇది యూజర్ నుండి విలువను తీసుకుంటుంది.",
        "output": "ఇది ఫలితాన్ని స్క్రీన్ మీద చూపిస్తుంది.",
        "array": "అర్రే ఒకే పేరుతో చాలా విలువలను వరుసగా నిల్వ చేస్తుంది.",
        "general": "ఈ లైన్ ప్రోగ్రామ్‌లో ఒక చిన్న దశను పూర్తి చేస్తుంది.",
    },
    "Hindi": {
        "blank": "यह खाली लाइन कोड को पढ़ना आसान बनाती है.",
        "comment": "यह एक कमेंट है. यह इंसानों के लिए कोड समझाता है और कंप्यूटर इसे नहीं चलाता.",
        "variable": "वेरिएबल डेटा रखने वाले छोटे डिब्बे की तरह काम करता है.",
        "loop": "लूप एक ही काम को बार-बार करने में मदद करता है.",
        "condition": "कंडीशन सही या गलत देखकर अगला फैसला लेती है.",
        "function": "फंक्शन किसी खास काम के लिए बनाया गया छोटा टूल है.",
        "input": "यह लाइन यूजर से जानकारी लेती है.",
        "output": "यह लाइन परिणाम को स्क्रीन पर दिखाती है.",
        "array": "अरे एक ही नाम से कई वैल्यू को क्रम में रखता है.",
        "general": "यह लाइन प्रोग्राम में एक छोटा कदम पूरा करती है.",
    },
    "Marathi": {
        "blank": "ही रिकामी ओळ कोड वाचायला सोपा करते.",
        "comment": "ही कमेंट आहे. ती माणसांसाठी कोड समजावते आणि संगणक ती चालवत नाही.",
        "variable": "व्हेरिएबल डेटा ठेवणाऱ्या छोट्या डब्यासारखे काम करते.",
        "loop": "लूप एकच काम पुन्हा पुन्हा करण्यासाठी वापरला जातो.",
        "condition": "कंडीशन खरे की खोटे तपासून पुढचा निर्णय घेते.",
        "function": "फंक्शन एखाद्या कामासाठी बनवलेले छोटे साधन आहे.",
        "input": "ही ओळ वापरकर्त्याकडून माहिती घेते.",
        "output": "ही ओळ निकाल स्क्रीनवर दाखवते.",
        "array": "अ‍ॅरे एकाच नावाखाली अनेक मूल्ये क्रमाने ठेवतो.",
        "general": "ही ओळ प्रोग्राममधील एक छोटा टप्पा पूर्ण करते.",
    },
    "Kannada": {
        "blank": "ಈ ಖಾಲಿ ಸಾಲು ಕೋಡ್ ಓದಲು ಸುಲಭವಾಗಿಸುತ್ತದೆ.",
        "comment": "ಇದು ಕಾಮೆಂಟ್. ಇದು ಮಾನವರಿಗೆ ಕೋಡ್ ವಿವರಿಸುತ್ತದೆ, ಕಂಪ್ಯೂಟರ್ ಇದನ್ನು ಚಾಲನೆ ಮಾಡುವುದಿಲ್ಲ.",
        "variable": "ವೇರಿಯಬಲ್ ಡೇಟಾವನ್ನು ಇಡುವ ಸಣ್ಣ ಪೆಟ್ಟಿಗೆಯಂತೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ.",
        "loop": "ಲೂಪ್ ಒಂದೇ ಕೆಲಸವನ್ನು ಮರುಮರು ಮಾಡಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
        "condition": "ಕಂಡಿಷನ್ ಸತ್ಯವೇ ಸುಳ್ಳೇ ಎಂದು ನೋಡಿ ಮುಂದಿನ ನಿರ್ಧಾರ ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ.",
        "function": "ಫಂಕ್ಷನ್ ಒಂದು ನಿರ್ದಿಷ್ಟ ಕೆಲಸಕ್ಕೆ ಮಾಡಿದ ಸಣ್ಣ ಸಾಧನದಂತಿದೆ.",
        "input": "ಈ ಸಾಲು ಬಳಕೆದಾರರಿಂದ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯುತ್ತದೆ.",
        "output": "ಈ ಸಾಲು ಫಲಿತಾಂಶವನ್ನು ಪರದೆಯ ಮೇಲೆ ತೋರಿಸುತ್ತದೆ.",
        "array": "ಅರೆ ಒಂದೇ ಹೆಸರಿನಲ್ಲಿ ಹಲವು ಮೌಲ್ಯಗಳನ್ನು ಕ್ರಮವಾಗಿ ಇಡುತ್ತದೆ.",
        "general": "ಈ ಸಾಲು ಪ್ರೋಗ್ರಾಂನಲ್ಲಿ ಒಂದು ಸಣ್ಣ ಹಂತವನ್ನು ಪೂರ್ಣಗೊಳಿಸುತ್ತದೆ.",
    },
    "Tamil": {
        "blank": "இந்த காலியான வரி கோடை எளிதாகப் படிக்க உதவுகிறது.",
        "comment": "இது ஒரு கருத்துரை. இது மனிதர்களுக்கு கோடை விளக்கும், கணினி இதை இயக்காது.",
        "variable": "மாறி என்பது தரவை வைத்திருக்கும் சிறிய பெட்டி போல செயல்படும்.",
        "loop": "லூப் ஒரே செயலை மீண்டும் மீண்டும் செய்ய உதவும்.",
        "condition": "நிபந்தனை உண்மையா பொய்யா என்று பார்த்து முடிவு எடுக்கிறது.",
        "function": "செயல்பாடு ஒரு குறிப்பிட்ட வேலையுக்கான சிறிய கருவி போன்றது.",
        "input": "இந்த வரி பயனரிடமிருந்து தகவலை பெறுகிறது.",
        "output": "இந்த வரி முடிவை திரையில் காட்டுகிறது.",
        "array": "அணி ஒரே பெயரில் பல மதிப்புகளை வரிசையாக வைத்திருக்கும்.",
        "general": "இந்த வரி நிரலில் ஒரு சிறிய படியை முடிக்கிறது.",
    },
}

SUMMARY_TRANSLATIONS = {
    "English": "This program follows small instructions to create a result.",
    "Telugu": "ఈ ప్రోగ్రామ్ చిన్న చిన్న సూచనలను అనుసరించి ఫలితాన్ని తయారు చేస్తుంది.",
    "Hindi": "यह प्रोग्राम छोटे-छोटे निर्देशों का पालन करके परिणाम बनाता है.",
    "Marathi": "हा प्रोग्राम छोटी छोटी सूचना पाळून निकाल तयार करतो.",
    "Kannada": "ಈ ಪ್ರೋಗ್ರಾಂ ಸಣ್ಣ ಸೂಚನೆಗಳನ್ನು ಅನುಸರಿಸಿ ಫಲಿತಾಂಶವನ್ನು ತಯಾರಿಸುತ್ತದೆ.",
    "Tamil": "இந்த நிரல் சிறிய வழிமுறைகளைப் பின்பற்றி ஒரு முடிவை உருவாக்குகிறது.",
}

ANALOGY_TRANSLATIONS = {
    "English": "Think of this code like a recipe: variables are ingredients, conditions are choices, loops repeat steps, and output is the final dish.",
    "Telugu": "ఈ కోడ్‌ను వంట రెసిపీలా ఊహించండి: వేరియబుల్స్ పదార్థాలు, కండిషన్స్ ఎంపికలు, లూప్స్ పునరావృత దశలు.",
    "Hindi": "इस कोड को रेसिपी की तरह सोचें: वेरिएबल सामग्री हैं, कंडीशन चुनाव हैं, लूप दोहराए जाने वाले कदम हैं.",
    "Marathi": "हा कोड रेसिपीसारखा समजा: व्हेरिएबल्स म्हणजे साहित्य, कंडीशन्स म्हणजे निवडी, आणि लूप्स म्हणजे पुन्हा होणारे टप्पे.",
    "Kannada": "ಈ ಕೋಡ್ ಅನ್ನು ಅಡುಗೆ ವಿಧಾನವಾಗಿ ಯೋಚಿಸಿ: ವೇರಿಯಬಲ್‌ಗಳು ಪದಾರ್ಥಗಳು, ಕಂಡಿಷನ್‌ಗಳು ಆಯ್ಕೆಗಳು, ಲೂಪ್‌ಗಳು ಮರುಕಳಿಸುವ ಹಂತಗಳು.",
    "Tamil": "இந்த கோடை சமையல் முறையாக நினைத்துக் கொள்ளுங்கள்: மாறிகள் பொருட்கள், நிபந்தனைகள் தேர்வுகள், லூப்புகள் மீண்டும் செய்யும் படிகள்.",
}


def get_db_connection():
    """Open a SQLite connection and return rows as dictionary-like objects."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create database tables if they do not already exist."""
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            skill_level TEXT DEFAULT '',
            language_preference TEXT DEFAULT ''
        )
        """
    )

    connection.commit()
    connection.close()


def current_user():
    """Return the logged-in user row, or None when the visitor is logged out."""
    user_id = session.get("user_id")
    if not user_id:
        return None

    connection = get_db_connection()
    user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    connection.close()
    return user


def login_required(view_function):
    """Simple decorator to protect pages that need a logged-in user."""
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    wrapped_view.__name__ = view_function.__name__
    return wrapped_view


def detect_language(code):
    """Guess the programming language using beginner-friendly pattern checks."""
    lowered = code.lower()

    if "#include" in code or "using namespace std" in lowered or "cout <<" in code or "cin >>" in code:
        return "C++"
    if "#include" in code or "printf(" in code or "scanf(" in code:
        return "C"
    if "function " in code or "console.log" in code or "let " in code or "const " in code:
        return "JavaScript"
    if "def " in code or "print(" in code or "input(" in code or re.search(r"^\s*for .+ in .+:", code, re.MULTILINE):
        return "Python"
    return "Unknown"


def selected_languages(preference):
    """Convert the dashboard dropdown value into languages to display."""
    if preference in ["Multiple Languages", "Both"]:
        return SUPPORTED_LANGUAGES
    if preference in SUPPORTED_LANGUAGES:
        return [preference]
    return ["English"]


def translated_for(kind, english):
    """Return one code concept explanation in every supported language."""
    explanations = {"English": english}
    for language, phrases in TRANSLATED_PHRASES.items():
        explanations[language] = phrases.get(kind, phrases["general"])
    return explanations


def classify_line(line):
    """Classify one line of code into a concept such as loop, variable, or function."""
    stripped = line.strip()

    if not stripped:
        return "blank", "This empty line makes the code easier to read."
    if stripped.startswith(("//", "#")):
        return "comment", "This is a comment. It explains the code for humans and is ignored by the computer."
    if re.search(r"\b(for|while)\b", stripped):
        return "loop", "This loop repeats a block of code until its rule is finished."
    if re.search(r"\b(if|else if|elif|else|switch)\b", stripped):
        return "condition", "This condition helps the program choose what to do next."
    if re.search(r"\b(def|function)\b|[a-zA-Z_]\w*\s+\w+\s*\([^)]*\)\s*\{?", stripped):
        return "function", "This line starts or describes a function, which groups reusable instructions."
    if re.search(r"\b(input|scanf|cin\s*>>|prompt)\b", stripped):
        return "input", "This line takes information from the user."
    if re.search(r"\b(print|printf|cout\s*<<|console\.log)\b", stripped):
        return "output", "This line shows a result to the user."
    if re.search(r"\[[^\]]*\]", stripped):
        return "array", "This line uses an array or list, which stores multiple values together."
    if re.search(r"\b(int|float|double|char|string|bool|var|let|const)\b|=", stripped):
        return "variable", "This line creates, updates, or uses a value stored in memory."
    return "general", "This line performs one step in the program."


def detect_errors(code, language):
    """Find common beginner mistakes and return friendly correction suggestions."""
    errors = []
    lines = code.splitlines()

    if language in ["C", "C++", "JavaScript"]:
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            skip_line = (
                not stripped
                or stripped.startswith(("//", "#"))
                or stripped.endswith((";", "{", "}", ":"))
                or re.match(r"^(if|for|while|else|switch|function)\b", stripped)
            )
            if not skip_line and re.search(r"\b(int|float|double|char|string|bool|let|const|var|printf|cout|console\.log)\b", stripped):
                errors.append(
                    {
                        "line": index,
                        "title": "Possible missing semicolon",
                        "message": "This line may need a semicolon at the end.",
                        "fix": "Add ';' at the end of the statement.",
                    }
                )

    bracket_pairs = [("{", "}"), ("(", ")"), ("[", "]")]
    for opening, closing in bracket_pairs:
        if code.count(opening) != code.count(closing):
            errors.append(
                {
                    "line": None,
                    "title": f"Unmatched {opening}{closing} brackets",
                    "message": "Opening and closing brackets should come in pairs.",
                    "fix": f"Check that every '{opening}' has a matching '{closing}'.",
                }
            )

    if language == "Python":
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if re.match(r"^(if|for|while|def|elif|else)\b", stripped) and not stripped.endswith(":"):
                errors.append(
                    {
                        "line": index,
                        "title": "Possible missing colon",
                        "message": "Python block statements usually end with ':'.",
                        "fix": "Add ':' at the end of the line.",
                    }
                )

    return errors


def build_explanation(code, preference, skill_mode="Beginner"):
    """Create the full AI-like explanation response for the dashboard."""
    language = detect_language(code)
    languages = selected_languages(preference)
    line_explanations = []

    for index, line in enumerate(code.splitlines(), start=1):
        kind, english = classify_line(line)
        explanations = translated_for(kind, english)
        line_explanations.append(
            {
                "number": index,
                "code": line,
                "type": kind,
                "explanations": {lang: explanations[lang] for lang in languages},
            }
        )

    concept_counts = {}
    for item in line_explanations:
        concept_counts[item["type"]] = concept_counts.get(item["type"], 0) + 1

    summary_parts = []
    if concept_counts.get("input"):
        summary_parts.append("takes input")
    if concept_counts.get("variable"):
        summary_parts.append("stores values")
    if concept_counts.get("condition"):
        summary_parts.append("makes decisions")
    if concept_counts.get("loop"):
        summary_parts.append("repeats work")
    if concept_counts.get("function"):
        summary_parts.append("organizes reusable logic")
    if concept_counts.get("output"):
        summary_parts.append("shows output")

    english_summary = "This program " + ", ".join(summary_parts) + "." if summary_parts else SUMMARY_TRANSLATIONS["English"]
    summaries = {language_name: SUMMARY_TRANSLATIONS[language_name] for language_name in languages}
    summaries["English"] = english_summary if "English" in languages else summaries.get("English", english_summary)
    analogies = {language_name: ANALOGY_TRANSLATIONS[language_name] for language_name in languages}

    mode_note = "Beginner mode uses simple words and everyday comparisons."
    if skill_mode == "Intermediate":
        mode_note = "Intermediate mode adds a little more programming vocabulary while staying clear."

    return {
        "language": language,
        "preference": preference,
        "skill_mode": skill_mode,
        "mode_note": mode_note,
        "selected_languages": languages,
        "lines": line_explanations,
        "errors": detect_errors(code, language),
        "summaries": summaries,
        "analogies": analogies,
    }


@app.route("/")
def index():
    """Show the clean animated welcome screen."""
    return render_template("index.html", user=current_user())


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Create a new user account."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template("signup.html", error="Please fill in all fields.")

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match.")

        connection = get_db_connection()
        try:
            cursor = connection.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            connection.commit()
            session["user_id"] = cursor.lastrowid
            return redirect(url_for("setup"))
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="An account with this email already exists.")
        finally:
            connection.close()

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in an existing user."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db_connection()
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            if user["skill_level"] and user["language_preference"]:
                return redirect(url_for("dashboard"))
            return redirect(url_for("setup"))

        return render_template("login.html", error="Invalid email or password.")

    success = request.args.get("success", "")
    return render_template("login.html", success=success)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Verify a registered email before allowing a local password reset."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        connection = get_db_connection()
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        connection.close()

        if not user:
            return render_template("forgot_password.html", error="Email not found.")

        session["reset_email"] = email
        return redirect(url_for("reset_password"))

    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Let a verified user create a new password without external email APIs."""
    reset_email = session.get("reset_email")
    if not reset_email:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or not confirm_password:
            return render_template("reset_password.html", email=reset_email, error="Please fill in all fields.")

        if password != confirm_password:
            return render_template("reset_password.html", email=reset_email, error="Passwords do not match.")

        connection = get_db_connection()
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (generate_password_hash(password), reset_email),
        )
        connection.commit()
        connection.close()

        session.pop("reset_email", None)
        return redirect(url_for("login", success="Password updated successfully."))

    return render_template("reset_password.html", email=reset_email)


@app.route("/logout")
def logout():
    """Clear the current session and return to the welcome page."""
    session.clear()
    return redirect(url_for("index"))


@app.route("/setup", methods=["GET", "POST"])
@login_required
def setup():
    """Collect skill level and explanation language preference."""
    user = current_user()

    if request.method == "POST":
        skill_level = request.form.get("skill_level", "Beginner")
        language_preference = request.form.get("language_preference", "Multiple Languages")

        connection = get_db_connection()
        connection.execute(
            "UPDATE users SET skill_level = ?, language_preference = ? WHERE id = ?",
            (skill_level, language_preference, user["id"]),
        )
        connection.commit()
        connection.close()
        return redirect(url_for("dashboard"))

    return render_template("setup.html", user=user)


@app.route("/dashboard")
@login_required
def dashboard():
    """Show the main AI Code Tutor dashboard."""
    user = current_user()
    return render_template("dashboard.html", user=user)


@app.route("/api/explain", methods=["POST"])
@login_required
def explain_code():
    """Receive code from JavaScript and return structured explanations."""
    user = current_user()
    payload = request.get_json() or {}
    code = payload.get("code", "").strip()
    preference = payload.get("preference") or user["language_preference"] or "Multiple Languages"
    skill_mode = payload.get("skill_mode") or user["skill_level"] or "Beginner"

    if not code:
        return jsonify({"error": "Please enter code before asking for an explanation."}), 400

    return jsonify(build_explanation(code, preference, skill_mode))


# Render starts the app by importing this file with Gunicorn, so initialize
# the local SQLite database at import time as well as during local runs.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
