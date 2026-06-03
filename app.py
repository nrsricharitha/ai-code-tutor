import json
import os
import re
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-production")

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "ai_code_tutor.db"

SUPPORTED_LANGUAGES = ["English", "Telugu", "Hindi", "Marathi", "Kannada", "Tamil"]

CONCEPT_TRANSLATIONS = {
    "variable": {
        "English": "This line stores or updates data using a variable.",
        "Telugu": "ఈ లైన్ వేరియబుల్ సహాయంతో డేటాను నిల్వ చేస్తుంది లేదా మార్చుతుంది.",
        "Hindi": "यह लाइन वेरिएबल की मदद से डेटा को रखती या बदलती है.",
        "Marathi": "ही ओळ व्हेरिएबलच्या मदतीने डेटा ठेवते किंवा बदलते.",
        "Kannada": "ಈ ಸಾಲು ವೇರಿಯಬಲ್ ಬಳಸಿ ಡೇಟಾವನ್ನು ಇಡುತ್ತದೆ ಅಥವಾ ಬದಲಿಸುತ್ತದೆ.",
        "Tamil": "இந்த வரி மாறி மூலம் தரவை சேமிக்கிறது அல்லது மாற்றுகிறது.",
    },
    "loop": {
        "English": "This line starts a loop, which repeats instructions.",
        "Telugu": "ఈ లైన్ లూప్‌ను ప్రారంభిస్తుంది. లూప్ సూచనలను మళ్లీ మళ్లీ నడిపిస్తుంది.",
        "Hindi": "यह लाइन लूप शुरू करती है, जो निर्देशों को बार-बार चलाता है.",
        "Marathi": "ही ओळ लूप सुरू करते, जो सूचना पुन्हा पुन्हा चालवतो.",
        "Kannada": "ಈ ಸಾಲು ಲೂಪ್ ಆರಂಭಿಸುತ್ತದೆ. ಲೂಪ್ ಸೂಚನೆಗಳನ್ನು ಮರುಮರು ನಡೆಸುತ್ತದೆ.",
        "Tamil": "இந்த வரி லூப்பை தொடங்குகிறது. லூப் கட்டளைகளை மீண்டும் செய்கிறது.",
    },
    "condition": {
        "English": "This line checks a condition and helps the program choose a path.",
        "Telugu": "ఈ లైన్ ఒక కండిషన్‌ను చూసి ప్రోగ్రామ్ ఏ దారిలో వెళ్లాలో నిర్ణయిస్తుంది.",
        "Hindi": "यह लाइन कंडीशन जांचती है और प्रोग्राम को रास्ता चुनने में मदद करती है.",
        "Marathi": "ही ओळ कंडीशन तपासते आणि प्रोग्रामला योग्य मार्ग निवडायला मदत करते.",
        "Kannada": "ಈ ಸಾಲು ಕಂಡಿಷನ್ ಪರಿಶೀಲಿಸಿ ಪ್ರೋಗ್ರಾಂ ಯಾವ ದಾರಿ ಹಿಡಿಯಬೇಕು ಎಂದು ನಿರ್ಧರಿಸುತ್ತದೆ.",
        "Tamil": "இந்த வரி நிபந்தனையை சரிபார்த்து நிரல் எந்த பாதையில் செல்ல வேண்டும் என்பதை தீர்மானிக்கிறது.",
    },
    "function": {
        "English": "This line defines or calls a function, which groups reusable code.",
        "Telugu": "ఈ లైన్ ఫంక్షన్‌ను నిర్వచిస్తుంది లేదా పిలుస్తుంది. ఫంక్షన్ మళ్లీ వాడే కోడ్‌ను గుంపుగా ఉంచుతుంది.",
        "Hindi": "यह लाइन फंक्शन को बनाती या चलाती है. फंक्शन दोबारा उपयोग होने वाला कोड रखता है.",
        "Marathi": "ही ओळ फंक्शन तयार करते किंवा चालवते. फंक्शन पुन्हा वापरता येणारा कोड ठेवते.",
        "Kannada": "ಈ ಸಾಲು ಫಂಕ್ಷನ್ ಅನ್ನು ರಚಿಸುತ್ತದೆ ಅಥವಾ ಕರೆಯುತ್ತದೆ. ಫಂಕ್ಷನ್ ಮರುಬಳಕೆ ಕೋಡ್ ಅನ್ನು ಗುಂಪಾಗಿಸುತ್ತದೆ.",
        "Tamil": "இந்த வரி செயல்பாட்டை உருவாக்குகிறது அல்லது அழைக்கிறது. செயல்பாடு மீண்டும் பயன்படுத்தும் கோடை குழுவாக வைத்திருக்கும்.",
    },
    "array": {
        "English": "This line uses an array or list to store many values together.",
        "Telugu": "ఈ లైన్ ఎన్నో విలువలను కలిపి నిల్వ చేయడానికి అర్రే లేదా లిస్ట్‌ను ఉపయోగిస్తుంది.",
        "Hindi": "यह लाइन कई वैल्यू को साथ रखने के लिए अरे या लिस्ट का उपयोग करती है.",
        "Marathi": "ही ओळ अनेक मूल्ये एकत्र ठेवण्यासाठी अ‍ॅरे किंवा लिस्ट वापरते.",
        "Kannada": "ಈ ಸಾಲು ಹಲವು ಮೌಲ್ಯಗಳನ್ನು ಒಟ್ಟಿಗೆ ಇಡಲು ಅರೆ ಅಥವಾ ಲಿಸ್ಟ್ ಬಳಸುತ್ತದೆ.",
        "Tamil": "இந்த வரி பல மதிப்புகளை ஒன்றாக சேமிக்க அணி அல்லது பட்டியலை பயன்படுத்துகிறது.",
    },
    "class": {
        "English": "This line creates a class, which is a blueprint for objects.",
        "Telugu": "ఈ లైన్ క్లాస్‌ను సృష్టిస్తుంది. క్లాస్ అనేది ఆబ్జెక్టుల కోసం బ్లూప్రింట్‌లాంటిది.",
        "Hindi": "यह लाइन क्लास बनाती है. क्लास ऑब्जेक्ट बनाने का ब्लूप्रिंट होती है.",
        "Marathi": "ही ओळ क्लास तयार करते. क्लास म्हणजे ऑब्जेक्टसाठी आराखडा असतो.",
        "Kannada": "ಈ ಸಾಲು ಕ್ಲಾಸ್ ರಚಿಸುತ್ತದೆ. ಕ್ಲಾಸ್ ಆಬ್ಜೆಕ್ಟ್‌ಗಳಿಗೆ ಬ್ಲೂಪ್ರಿಂಟ್ ಆಗಿದೆ.",
        "Tamil": "இந்த வரி class-ஐ உருவாக்குகிறது. Class என்பது object-களுக்கான வரைபடம் போன்றது.",
    },
    "object": {
        "English": "This line creates or uses an object, which stores data and behavior together.",
        "Telugu": "ఈ లైన్ ఆబ్జెక్ట్‌ను సృష్టిస్తుంది లేదా ఉపయోగిస్తుంది. ఆబ్జెక్ట్ డేటా మరియు పనులను కలిపి ఉంచుతుంది.",
        "Hindi": "यह लाइन ऑब्जेक्ट बनाती या उपयोग करती है. ऑब्जेक्ट डेटा और व्यवहार को साथ रखता है.",
        "Marathi": "ही ओळ ऑब्जेक्ट तयार करते किंवा वापरते. ऑब्जेक्ट डेटा आणि वर्तन एकत्र ठेवतो.",
        "Kannada": "ಈ ಸಾಲು ಆಬ್ಜೆಕ್ಟ್ ರಚಿಸುತ್ತದೆ ಅಥವಾ ಬಳಸುತ್ತದೆ. ಆಬ್ಜೆಕ್ಟ್ ಡೇಟಾ ಮತ್ತು ವರ್ತನೆಯನ್ನು ಒಟ್ಟಿಗೆ ಇಡುತ್ತದೆ.",
        "Tamil": "இந்த வரி object-ஐ உருவாக்குகிறது அல்லது பயன்படுத்துகிறது. Object தரவு மற்றும் செயல்களை ஒன்றாக வைத்திருக்கும்.",
    },
    "recursion": {
        "English": "This line suggests recursion, where a function calls itself.",
        "Telugu": "ఈ లైన్ రికర్షన్‌ను సూచిస్తుంది. రికర్షన్‌లో ఫంక్షన్ తనను తానే పిలుస్తుంది.",
        "Hindi": "यह लाइन रिकर्शन दिखाती है, जहां फंक्शन खुद को ही कॉल करता है.",
        "Marathi": "ही ओळ रिकर्शन दाखवते, जिथे फंक्शन स्वतःलाच कॉल करते.",
        "Kannada": "ಈ ಸಾಲು ರಿಕರ್ಷನ್ ಸೂಚಿಸುತ್ತದೆ. ರಿಕರ್ಷನ್‌ನಲ್ಲಿ ಫಂಕ್ಷನ್ ತನ್ನನ್ನೇ ಕರೆಯುತ್ತದೆ.",
        "Tamil": "இந்த வரி recursion-ஐ குறிக்கிறது. Recursion-ல் function தன்னையே அழைக்கிறது.",
    },
    "input": {
        "English": "This line takes input from the user.",
        "Telugu": "ఈ లైన్ యూజర్ నుండి ఇన్‌పుట్ తీసుకుంటుంది.",
        "Hindi": "यह लाइन यूजर से इनपुट लेती है.",
        "Marathi": "ही ओळ वापरकर्त्याकडून इनपुट घेते.",
        "Kannada": "ಈ ಸಾಲು ಬಳಕೆದಾರರಿಂದ ಇನ್‌ಪುಟ್ ಪಡೆಯುತ್ತದೆ.",
        "Tamil": "இந்த வரி பயனரிடமிருந்து input பெறுகிறது.",
    },
    "output": {
        "English": "This line displays output on the screen.",
        "Telugu": "ఈ లైన్ ఫలితాన్ని స్క్రీన్‌పై చూపిస్తుంది.",
        "Hindi": "यह लाइन स्क्रीन पर आउटपुट दिखाती है.",
        "Marathi": "ही ओळ स्क्रीनवर आउटपुट दाखवते.",
        "Kannada": "ಈ ಸಾಲು ಪರದೆಯ ಮೇಲೆ ಔಟ್‌ಪುಟ್ ತೋರಿಸುತ್ತದೆ.",
        "Tamil": "இந்த வரி திரையில் output காட்டுகிறது.",
    },
    "general": {
        "English": "This line performs one small step in the program.",
        "Telugu": "ఈ లైన్ ప్రోగ్రామ్‌లో ఒక చిన్న దశను పూర్తి చేస్తుంది.",
        "Hindi": "यह लाइन प्रोग्राम में एक छोटा कदम पूरा करती है.",
        "Marathi": "ही ओळ प्रोग्राममधील एक छोटा टप्पा पूर्ण करते.",
        "Kannada": "ಈ ಸಾಲು ಪ್ರೋಗ್ರಾಂನಲ್ಲಿ ಒಂದು ಸಣ್ಣ ಹಂತವನ್ನು ಪೂರ್ಣಗೊಳಿಸುತ್ತದೆ.",
        "Tamil": "இந்த வரி நிரலில் ஒரு சிறிய படியை முடிக்கிறது.",
    },
}


def get_db_connection():
    """Open a SQLite connection and return rows as dictionary-like objects."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create all database tables needed by the app."""
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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            preference TEXT NOT NULL,
            skill_mode TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_explanations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            history_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, history_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (history_id) REFERENCES analysis_history (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS progress_tracking (
            user_id INTEGER PRIMARY KEY,
            programs_analyzed INTEGER DEFAULT 0,
            total_explanations INTEGER DEFAULT 0,
            concepts_json TEXT DEFAULT '[]',
            current_level TEXT DEFAULT 'Beginner',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )

    connection.commit()
    connection.close()


def current_user():
    """Return the logged-in user, or None when logged out."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    connection = get_db_connection()
    user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    connection.close()
    return user


def login_required(view_function):
    """Protect routes that require a login."""
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    wrapped_view.__name__ = view_function.__name__
    return wrapped_view


def detect_language(code):
    """Detect the most likely programming language."""
    lowered = code.lower()
    if "public static void main" in lowered or "system.out.println" in lowered:
        return "Java"
    if "#include" in code and ("cout <<" in code or "cin >>" in code or "using namespace std" in lowered):
        return "C++"
    if "#include" in code or "printf(" in code or "scanf(" in code:
        return "C"
    if "function " in code or "console.log" in code or re.search(r"\b(let|const|var)\s+\w+", code):
        return "JavaScript"
    if "def " in code or "print(" in code or "input(" in code or re.search(r"^\s*for .+ in .+:", code, re.MULTILINE):
        return "Python"
    return "Unknown"


def selected_languages(preference):
    """Convert a dropdown preference into languages to display."""
    if preference in ["Multiple Languages", "Both"]:
        return SUPPORTED_LANGUAGES
    if preference in SUPPORTED_LANGUAGES:
        return [preference]
    return ["English"]


def classify_line(line):
    """Classify one line and return concept keys."""
    stripped = line.strip()
    concepts = []

    if not stripped:
        return ["general"]
    if stripped.startswith(("//", "#")):
        return ["general"]
    if re.search(r"\b(for|while|do)\b", stripped):
        concepts.append("loop")
    if re.search(r"\b(if|else if|elif|else|switch|case)\b", stripped):
        concepts.append("condition")
    if re.search(r"\b(def|function)\b|[a-zA-Z_]\w*\s+\w+\s*\([^)]*\)\s*\{?", stripped):
        concepts.append("function")
    if re.search(r"\bclass\b", stripped):
        concepts.append("class")
    if re.search(r"\bnew\s+[A-Z]\w*\s*\(", stripped):
        concepts.append("object")
    if re.search(r"\b(input|scanf|cin\s*>>|prompt)\b", stripped):
        concepts.append("input")
    if re.search(r"\b(print|printf|cout\s*<<|console\.log|System\.out\.println)\b", stripped):
        concepts.append("output")
    if re.search(r"\[[^\]]*\]", stripped):
        concepts.append("array")
    if re.search(r"\b(int|float|double|char|string|String|boolean|bool|var|let|const)\b|=", stripped):
        concepts.append("variable")

    # A simple recursion hint: a function-like name appears before and inside parentheses.
    function_names = re.findall(r"\b(?:def|function|int|void|public|private|static)\s+([A-Za-z_]\w*)\s*\(", stripped)
    if function_names and any(name + "(" in stripped[stripped.find("("):] for name in function_names):
        concepts.append("recursion")

    return concepts or ["general"]


def line_explanations_for(concepts):
    """Create translated explanations for a line from its detected concepts."""
    result = {}
    primary = concepts[0] if concepts else "general"
    for language in SUPPORTED_LANGUAGES:
        result[language] = CONCEPT_TRANSLATIONS.get(primary, CONCEPT_TRANSLATIONS["general"])[language]
    return result


def detect_errors(code, language):
    """Detect common beginner syntax mistakes."""
    errors = []
    lines = code.splitlines()

    if language in ["C", "C++", "Java", "JavaScript"]:
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            skip = (
                not stripped
                or stripped.startswith(("//", "#"))
                or stripped.endswith((";", "{", "}", ":"))
                or re.match(r"^(if|for|while|else|switch|class|public|private|function)\b", stripped)
            )
            if not skip and re.search(r"\b(int|float|double|char|string|String|boolean|bool|let|const|var|printf|cout|console\.log|System\.out\.println)\b", stripped):
                errors.append({
                    "line": index,
                    "title": "Possible missing semicolon",
                    "message": "This statement may need a semicolon at the end.",
                    "fix": "Add ';' after the statement.",
                })

    for opening, closing in [("{", "}"), ("(", ")"), ("[", "]")]:
        if code.count(opening) != code.count(closing):
            errors.append({
                "line": None,
                "title": f"Unmatched {opening}{closing} brackets",
                "message": "Opening and closing brackets should be balanced.",
                "fix": f"Check that every '{opening}' has a matching '{closing}'.",
            })

    if language == "Python":
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if re.match(r"^(if|for|while|def|elif|else|class)\b", stripped) and not stripped.endswith(":"):
                errors.append({
                    "line": index,
                    "title": "Possible missing colon",
                    "message": "Python block statements usually end with ':'.",
                    "fix": "Add ':' at the end of the line.",
                })
    return errors


def predict_output(code, language):
    """Predict simple outputs from common print statements."""
    patterns = [
        r'print\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'console\.log\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'System\.out\.println\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'printf\s*\(\s*["\']([^"\'%]+)["\']\s*\)',
        r'cout\s*<<\s*["\']([^"\']+)["\']',
    ]
    outputs = []
    for pattern in patterns:
        outputs.extend(re.findall(pattern, code))
    return "\n".join(outputs) if outputs else "Output prediction is not certain for this code."


def analyze_complexity(code, concepts):
    """Return a beginner-friendly complexity level and 1-10 score."""
    score = 1
    score += min(len(code.splitlines()) // 5, 3)
    score += 1 if "loop" in concepts else 0
    score += 1 if "condition" in concepts else 0
    score += 1 if "function" in concepts else 0
    score += 1 if "array" in concepts else 0
    score += 2 if "class" in concepts or "object" in concepts else 0
    score += 2 if "recursion" in concepts else 0
    score = min(score, 10)
    if score <= 3:
        level = "Beginner"
    elif score <= 6:
        level = "Intermediate"
    else:
        level = "Advanced"
    return {"level": level, "score": score}


def learning_roadmap(concepts):
    """Suggest next topics based on missing concepts."""
    topic_map = {
        "variable": "Variables and Data Types",
        "condition": "If-Else Conditions",
        "loop": "Loops",
        "function": "Functions",
        "array": "Arrays and Lists",
        "class": "Object-Oriented Programming",
        "object": "Objects",
        "recursion": "Recursion",
    }
    missing = [topic for key, topic in topic_map.items() if key not in concepts]
    return missing[:5] or ["Data Structures", "Algorithms", "Debugging Practice"]


def generate_quiz(concepts, language, output):
    """Generate simple quiz questions from detected code concepts."""
    questions = []
    if "loop" in concepts:
        questions.append("What does the loop repeat?")
    if "variable" in concepts:
        questions.append("Which variables store important values?")
    if "condition" in concepts:
        questions.append("What decision does the condition make?")
    if "function" in concepts:
        questions.append("What task does the function perform?")
    if output and "not certain" not in output:
        questions.append("What is the expected output?")
    questions.append(f"Which programming language was detected as {language}?")
    return questions[:5]


def build_explanation(code, preference, skill_mode="Beginner"):
    """Analyze code and return a complete structured result."""
    language = detect_language(code)
    display_languages = selected_languages(preference)
    lines = []
    detected = set()

    for number, line in enumerate(code.splitlines(), start=1):
        concepts = classify_line(line)
        detected.update(concept for concept in concepts if concept != "general")
        explanations = line_explanations_for(concepts)
        if skill_mode == "Intermediate":
            for lang in explanations:
                explanations[lang] += " It is useful for understanding program flow."
        lines.append({
            "number": number,
            "code": line,
            "concepts": concepts,
            "explanations": explanations,
        })

    concepts_list = sorted(detected)
    complexity = analyze_complexity(code, concepts_list)
    output = predict_output(code, language)
    errors = detect_errors(code, language)
    roadmap = learning_roadmap(concepts_list)
    quiz = generate_quiz(concepts_list, language, output)

    summaries = {
        "English": f"This {language} program uses {', '.join(concepts_list) if concepts_list else 'basic instructions'} to complete its task.",
        "Telugu": "ఈ ప్రోగ్రామ్ చిన్న చిన్న సూచనలను ఉపయోగించి పని పూర్తి చేస్తుంది.",
        "Hindi": "यह प्रोग्राम छोटे निर्देशों का उपयोग करके अपना काम पूरा करता है.",
        "Marathi": "हा प्रोग्राम छोट्या सूचनांचा वापर करून आपले काम पूर्ण करतो.",
        "Kannada": "ಈ ಪ್ರೋಗ್ರಾಂ ಸಣ್ಣ ಸೂಚನೆಗಳನ್ನು ಬಳಸಿ ತನ್ನ ಕೆಲಸವನ್ನು ಪೂರ್ಣಗೊಳಿಸುತ್ತದೆ.",
        "Tamil": "இந்த நிரல் சிறிய கட்டளைகளை பயன்படுத்தி தனது பணியை முடிக்கிறது.",
    }

    return {
        "language": language,
        "preference": preference,
        "skill_mode": skill_mode,
        "selected_languages": display_languages,
        "supported_languages": SUPPORTED_LANGUAGES,
        "lines": lines,
        "concepts": concepts_list,
        "complexity": complexity,
        "expected_output": output,
        "errors": errors,
        "roadmap": roadmap,
        "quiz": quiz,
        "summaries": summaries,
    }


def ensure_progress(user_id):
    """Create a progress row if the user does not have one."""
    connection = get_db_connection()
    connection.execute(
        "INSERT OR IGNORE INTO progress_tracking (user_id) VALUES (?)",
        (user_id,),
    )
    connection.commit()
    connection.close()


def update_progress(user_id, concepts, complexity_level):
    """Update progress counters after an analysis."""
    ensure_progress(user_id)
    connection = get_db_connection()
    progress = connection.execute(
        "SELECT * FROM progress_tracking WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    learned = set(json.loads(progress["concepts_json"] or "[]"))
    learned.update(concepts)
    connection.execute(
        """
        UPDATE progress_tracking
        SET programs_analyzed = programs_analyzed + 1,
            total_explanations = total_explanations + 1,
            concepts_json = ?,
            current_level = ?
        WHERE user_id = ?
        """,
        (json.dumps(sorted(learned)), complexity_level, user_id),
    )
    connection.commit()
    connection.close()


def get_progress(user_id):
    """Return progress data for the dashboard."""
    ensure_progress(user_id)
    connection = get_db_connection()
    progress = connection.execute(
        "SELECT * FROM progress_tracking WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    connection.close()
    concepts = json.loads(progress["concepts_json"] or "[]")
    return {
        "programs_analyzed": progress["programs_analyzed"],
        "total_explanations": progress["total_explanations"],
        "concepts_learned": concepts,
        "current_level": progress["current_level"],
    }


@app.route("/")
def index():
    return render_template("index.html", user=current_user())


@app.route("/signup", methods=["GET", "POST"])
def signup():
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
            session.clear()
            session["user_id"] = cursor.lastrowid
            ensure_progress(cursor.lastrowid)
            return redirect(url_for("setup"))
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="An account with this email already exists.")
        finally:
            connection.close()
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        connection = get_db_connection()
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        connection.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            ensure_progress(user["id"])
            if user["skill_level"] and user["language_preference"]:
                return redirect(url_for("dashboard"))
            return redirect(url_for("setup"))
        return render_template("login.html", error="Invalid email or password.")
    return render_template("login.html", success=request.args.get("success", ""))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
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


@app.route("/setup", methods=["GET", "POST"])
@login_required
def setup():
    user = current_user()
    if request.method == "POST":
        skill_level = request.form.get("skill_level", "Beginner")
        language_preference = request.form.get("language_preference", "English")
        connection = get_db_connection()
        connection.execute(
            "UPDATE users SET skill_level = ?, language_preference = ? WHERE id = ?",
            (skill_level, language_preference, user["id"]),
        )
        connection.commit()
        connection.close()
        return redirect(url_for("dashboard"))
    return render_template("setup.html", user=user, languages=SUPPORTED_LANGUAGES)


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return render_template("dashboard.html", user=user, progress=get_progress(user["id"]))


@app.route("/api/explain", methods=["POST"])
@login_required
def explain_code():
    user = current_user()
    payload = request.get_json() or {}
    code = payload.get("code", "").strip()
    preference = payload.get("preference") or user["language_preference"] or "English"
    skill_mode = payload.get("skill_mode") or user["skill_level"] or "Beginner"
    if not code:
        return jsonify({"error": "Please enter code before asking for an explanation."}), 400

    result = build_explanation(code, preference, skill_mode)
    connection = get_db_connection()
    cursor = connection.execute(
        """
        INSERT INTO analysis_history (user_id, code, language, preference, skill_mode, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user["id"], code, result["language"], preference, skill_mode, json.dumps(result, ensure_ascii=False)),
    )
    connection.commit()
    history_id = cursor.lastrowid
    connection.close()

    update_progress(user["id"], result["concepts"], result["complexity"]["level"])
    result["history_id"] = history_id
    result["progress"] = get_progress(user["id"])
    return jsonify(result)


@app.route("/api/history")
@login_required
def history():
    user = current_user()
    connection = get_db_connection()
    rows = connection.execute(
        """
        SELECT h.id, h.language, h.preference, h.created_at, h.code,
               CASE WHEN s.id IS NULL THEN 0 ELSE 1 END AS is_favorite
        FROM analysis_history h
        LEFT JOIN saved_explanations s ON s.history_id = h.id AND s.user_id = h.user_id
        WHERE h.user_id = ?
        ORDER BY h.created_at DESC
        LIMIT 20
        """,
        (user["id"],),
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/history/<int:history_id>")
@login_required
def history_detail(history_id):
    user = current_user()
    connection = get_db_connection()
    row = connection.execute(
        "SELECT * FROM analysis_history WHERE id = ? AND user_id = ?",
        (history_id, user["id"]),
    ).fetchone()
    favorite = connection.execute(
        "SELECT id FROM saved_explanations WHERE history_id = ? AND user_id = ?",
        (history_id, user["id"]),
    ).fetchone()
    connection.close()
    if not row:
        return jsonify({"error": "History item not found."}), 404
    result = json.loads(row["result_json"])
    result["history_id"] = row["id"]
    result["is_favorite"] = bool(favorite)
    result["code"] = row["code"]
    return jsonify(result)


@app.route("/api/favorite/<int:history_id>", methods=["POST"])
@login_required
def favorite(history_id):
    user = current_user()
    connection = get_db_connection()
    row = connection.execute(
        "SELECT id, language FROM analysis_history WHERE id = ? AND user_id = ?",
        (history_id, user["id"]),
    ).fetchone()
    if not row:
        connection.close()
        return jsonify({"error": "History item not found."}), 404
    existing = connection.execute(
        "SELECT id FROM saved_explanations WHERE history_id = ? AND user_id = ?",
        (history_id, user["id"]),
    ).fetchone()
    if existing:
        connection.execute("DELETE FROM saved_explanations WHERE id = ?", (existing["id"],))
        saved = False
    else:
        connection.execute(
            "INSERT INTO saved_explanations (user_id, history_id, title) VALUES (?, ?, ?)",
            (user["id"], history_id, f"{row['language']} explanation"),
        )
        saved = True
    connection.commit()
    connection.close()
    return jsonify({"saved": saved})


@app.route("/api/favorites")
@login_required
def favorites():
    user = current_user()
    connection = get_db_connection()
    rows = connection.execute(
        """
        SELECT s.id, s.history_id, s.title, s.created_at, h.language, h.code
        FROM saved_explanations s
        JOIN analysis_history h ON h.id = s.history_id
        WHERE s.user_id = ?
        ORDER BY s.created_at DESC
        """,
        (user["id"],),
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


init_db()


if __name__ == "__main__":
    app.run(debug=True)
