from functools import wraps
import html
import json
import os
import re
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ai-code-tutor-dev-secret")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

EXPLANATION_LANGUAGES = {
    "english": "English",
    "telugu": "Telugu",
    "hindi": "Hindi",
    "marathi": "Marathi",
    "kannada": "Kannada",
    "tamil": "Tamil",
}

SETUP_LANGUAGES = {
    **EXPLANATION_LANGUAGES,
    "multiple": "Multiple Languages",
}

SKILL_LEVELS = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}

CODE_LANGUAGES = {
    "auto": "Auto Detect",
    "python": "Python",
    "c": "C",
    "cpp": "C++",
    "java": "Java",
    "javascript": "JavaScript",
}

# Core Multilingual Teacher Dictionary (Analogies + Explanations mapped per concept)
TRANSLATIONS = {
    "english": {
        "overview": "Processed {language} architectural segment containing {lines} instructional block nodes.",
        "overview_empty": "Provide your lesson code structure files to instantiate tutor tracking frames.",
        "line": "Line {line}",
        "no_errors": "No obvious syntax structural flaws were found in this code segment.",
        "output_unknown": "Execution path cannot be reliably inferred dynamically.",
        "generic": "This line moves our program's structural workflow sequence forward.",
        "variable": "Variable Detected: '{name}' | Data Type: {dtype}. Purpose: Stores value in memory workspace. Why Used: Think of this like a labeled storage box. It allows our program to access or change this value later by simply calling its name.",
        "condition": "Decision Node Detected. Purpose: Checks a true/false condition statement. Why Used: Works just like a crossroad analogy. If the condition is true, the program takes this path; otherwise, it skips it.",
        "loop": "Loop Repetition Mechanism. Purpose: Repeatedly runs a block of code commands. Why Used: Saves you from writing the exact same lines of code over and over again. It runs until its ending rule finishes.",
        "print": "Output Command. Purpose: Displays text data or variable values directly onto the user screen. Why Used: Essential for communication. Without this, your program's results would stay hidden inside your computer's memory chip.",
        "intermediate_suffix": " [Control flow and data state adjustments apply to this frame layout.]",
        "advanced_suffix": " [Consider resource footprint optimizations and micro-register boundaries here.]"
    },
    "telugu": {
        "overview": "{language} కోడ్ {lines} లైన్లు కలిగి ఉంది.",
        "overview_empty": "పాఠాన్ని ప్రారంభించడానికి కోడ్ ముక్కను అందించండి.",
        "line": "లైన్ {line}",
        "no_errors": "నిర్మాణాత్మక లోపాలు ఏవీ కనుగొనబడలేదు.",
        "output_unknown": "అవుట్‌పుట్‌ను అంచనా వేయడం సాధ్యం కాలేదు.",
        "generic": "ఈ లైన్ ప్రోగ్రామ్ యొక్క తదుపరి దశను నడుపుతుంది.",
        "variable": "వేరియబుల్ కనుగొనబడింది: '{name}' | డేటా టైప్: {dtype}. ఉపయోగం: మెమరీలో విలువను దాచుకుంటుంది. ఎందుకు వాడతాం: దీనిని ఒక లేబుల్ ఉన్న పెట్టెలా అనుకోవచ్చు. ప్రోగ్రామ్‌లో ఎప్పుడైనా ఈ విలువను మార్చడానికి లేదా తిరిగి పొందడానికి ఇది సహాయపడుతుంది.",
        "condition": "నిర్ణయ దశ (Condition). ఉపయోగం: ఒక షరతు నిజమా కాదా అని తనిఖీ చేస్తుంది. ఎందుకు వాడతాం: ఒక రహదారి కూడలి లాంటిది. షరతు నిజమైతేనే ప్రోగ్రామ్ ఈ మార్గంలో వెళ్తుంది.",
        "loop": "లూప్ (Loop) మెకానిజం. ఉపయోగం: ఒకే కోడ్‌ను మళ్లీ మళ్లీ రన్ చేస్తుంది. ఎందుకు వాడతాం: ఒకే పనిని పదే పదే రాయకుండా సమయాన్ని ఆదా చేస్తుంది. ముగింపు నిబంధన వచ్చే వరకు ఇది రన్ అవుతుంది.",
        "print": "అవుట్‌పుట్ కమాండ్. ఉపయోగం: స్క్రీన్ మీద సమాచారాన్ని చూపిస్తుంది. ఎందుకు వాడతాం: యూజర్‌కు ప్రోగ్రామ్ ఫలితాన్ని చూపించడానికి ఇది చాలా ముఖ్యం.",
        "intermediate_suffix": " [ఇంటర్మీడియట్ స్థాయి: ఇక్కడ కంట్రోల్ ఫ్లో మారుతుంది.]",
        "advanced_suffix": " [అడ్వాన్స్డ్ స్థాయి: ఆప్టిమైజేషన్ మరియు ఎడ్జ్ కేసెస్ పరిశీలించండి.]"
    },
    "hindi": {
        "overview": "{language} कोड में {lines} लाइनें हैं।",
        "overview_empty": "पाठ शुरू करने के लिए कोड डालें।",
        "line": "लाइन {line}",
        "no_errors": "कोई स्पष्ट संरचनात्मक त्रुटि नहीं मिली।",
        "output_unknown": "आउटपुट का अनुमान नहीं लगाया जा सकता।",
        "generic": "यह लाइन प्रोग्राम के लॉजिक को आगे बढ़ाती है।",
        "variable": "वेरिएबल मिला: '{name}' | डेटा टाइप: {dtype}. उद्देश्य: वैल्यू को मेमोरी में स्टोर करता है। क्यों उपयोग करें: इसे एक लेबल वाले बॉक्स की तरह समझें। यह हमारे प्रोग्राम को बाद में इसका नाम लेकर वैल्यू तक पहुंचने या बदलने की अनुमति देता है।",
        "condition": "निर्णय बिंदु (Condition). उद्देश्य: यह जांचता है कि शर्त सही है या गलत। क्यों उपयोग करें: एक चौराहे की तरह काम करता है। यदि शर्त सही है, तो प्रोग्राम इस रास्ते पर चलता है।",
        "loop": "लूप (Loop) प्रक्रिया। उद्देश्य: कोड के एक हिस्से को बार-बार चलाता है। क्यों उपयोग करें: आपको एक ही कोड बार-बार लिखने से बचाता है। यह तब तक चलता है जब तक इसकी अंतिम शर्त पूरी नहीं हो जाती।",
        "print": "आउटपुट कमांड। उद्देश्य: स्क्रीन पर टेक्स्ट या वेरिएबल की वैल्यू दिखाता है। क्यों उपयोग करें: यह उपयोगकर्ता के साथ बातचीत के लिए आवश्यक है, इसके बिना परिणाम कंप्यूटर मेमोरी में छिपे रहेंगे।",
        "intermediate_suffix": " [मध्यम स्तर: ध्यान दें कि यहां डेटा की स्थिति कैसे बदलती है।]",
        "advanced_suffix": " [उच्च स्तर: यहां समय/स्थान जटिलता और अनुकूलन पर विचार करें।]"
    },
    "marathi": {
        "overview": "{language} कोडमध्ये {lines} ओळी आहेत.",
        "overview_empty": "धडा सुरू करण्यासाठी कोड प्रविष्ट करा.",
        "line": "ओळ {line}",
        "no_errors": "कोणतीही त्रुटी आढळली नाही.",
        "output_unknown": "आउटपुटचा अंदाज लावता येत नाही.",
        "generic": "ही ओळ प्रोग्रामचे लॉजिक पुढे नेते.",
        "variable": "व्हेरिएबल सापडला: '{name}' | डेटा टाईप: {dtype}. उद्देश: मेमरीमध्ये मूल्य साठवतो. का वापरावे: हे एका लेबल असलेल्या बॉक्ससारखे आहे. हे आपल्याला नंतर फक्त त्याचे नाव वापरून मूल्य बदलण्याची परवानगी देते.",
        "condition": "निर्णय बिंदू (Condition). उद्देश: अट खरी आहे की खोटे हे तपासते. का वापरावे: एका चौकासारखे काम करते. अट खरी असेल तरच प्रोग्राम या मार्गाने जातो.",
        "loop": "लूप (Loop) प्रक्रिया. उद्देश: कोडचा भाग पुन्हा पुन्हा चालवतो. का वापरावे: आपल्याला एकच कोड वारंवार लिहिण्यापासून वाचवते. शेवटची अट पूर्ण होईपर्यंत हे चालू राहते.",
        "print": "आउटपुट कमांड. उद्देश: स्क्रीनवर मजकूर किंवा मूल्य दाखवते. का वापरावे: युझरला निकाल दाखवण्यासाठी हे आवश्यक आहे.",
        "intermediate_suffix": " [मध्यम स्तर: नियंत्रण प्रवाह आणि डेटा बदल येथे पहा.]",
        "advanced_suffix": " [प्रगत स्तर: कार्यक्षमता आणि ऑप्टिमायझेशनचा विचार करा.]"
    },
    "kannada": {
        "overview": "{language} ಕೋಡ್ {lines} ಸಾಲುಗಳನ್ನು ಹೊಂದಿದೆ.",
        "overview_empty": "ಪಾಠವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಕೋಡ್ ನಮೂದಿಸಿ.",
        "line": "ಸಾಲು {line}",
        "no_errors": "ಯಾವುದೇ ದೋಷ ಕಂಡುಬಂದಿಲ್ಲ.",
        "output_unknown": "ಔಟ್‌ಪುಟ್ ಊಹಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "generic": "ಈ ಸಾಲು ಪ್ರೋಗ್ರಾಂನ ಮುಂದಿನ ಹಂತವನ್ನು ರನ್ ಮಾಡುತ್ತದೆ.",
        "variable": "ವೇರಿಯಬಲ್ ಪತ್ತೆಯಾಗಿದೆ: '{name}' | ಡೇಟಾ ಟೈಪ್: {dtype}. ಉದ್ದೇಶ: ಮೆಮೊರಿಯಲ್ಲಿ ಮೌಲ್ಯವನ್ನು ಸಂಗ್ರಹಿಸುತ್ತದೆ. ಏಕೆ ಬಳಸಬೇಕು: ಇದನ್ನು ಲೇಬಲ್ ಇರುವ ಪೆಟ್ಟಿಗೆಯಂತೆ ಯೋಚಿಸಿ. ಇದು ಪ್ರೋಗ್ರಾಂನಲ್ಲಿ ಮೌಲ್ಯವನ್ನು ಬದಲಾಯಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.",
        "condition": "ನಿರ್ಧಾರದ ಹಂತ (Condition). ಉದ್ದೇಶ: ಸ್ಥಿತಿಯು ನಿಜವೇ ಅಥವಾ ಸುಳ್ಳೇ ಎಂದು ಪರಿಶೀಲಿಸುತ್ತದೆ. ಏಕೆ ಬಳಸಬೇಕು: ಒಂದು ಅಡ್ಡರಸ್ತೆಯಂತೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ. ಸ್ಥಿತಿ ನಿಜವಾಗಿದ್ದರೆ ಮಾತ್ರ ಪ್ರೋಗ್ರಾಂ ಈ ಹಾದಿಯಲ್ಲಿ ಹೋಗುತ್ತದೆ.",
        "loop": "ಲೂಪ್ (Loop) ಕಾರ್ಯವಿಧಾನ. ಉದ್ದೇಶ: ಕೋಡ್ ಅನ್ನು ಪದೇ ಪದೇ ರನ್ ಮಾಡುತ್ತದೆ. ಏಕೆ ಬಳಸಬೇಕು: ಒಂದೇ ಕೋಡ್ ಅನ್ನು ಮತ್ತೆ ಮತ್ತೆ ಬರೆಯುವುದರಿಂದ ನಿಮ್ಮನ್ನು ಉಳಿಸುತ್ತದೆ.",
        "print": "ಔಟ್‌ಪುಟ್ ಕಮಾಂಡ್. ಉದ್ದೇಶ: ಪರದೆಯ ಮೇಲೆ ಫಲಿತಾಂಶವನ್ನು ತೋರಿಸುತ್ತದೆ. ಏಕೆ ಬಳಸಬೇಕು: ಬಳಕೆದಾರರಿಗೆ ಪ್ರೋಗ್ರಾಂ ಫಲಿತಾಂಶವನ್ನು ತೋರಿಸಲು ಇದು ಅತ್ಯಗತ್ಯ.",
        "intermediate_suffix": " [ಮಧ್ಯಂತರ ಮಟ್ಟ: ಇಲ್ಲಿ ನಿಯಂತ್ರಣ ಹರಿವು ಬದಲಾಗುತ್ತದೆ.]",
        "advanced_suffix": " [ಸುಧಾರಿತ ಮಟ್ಟ: ಆಪ್ಟಿಮೈಸೇಶನ್ ಪರಿಶೀಲಿಸಿ.]"
    },
    "tamil": {
        "overview": "{language} குறியீடு {lines} வரிகளைக் கொண்டுள்ளது.",
        "overview_empty": "பாடத்தைத் தொடங்க குறியீட்டை உள்ளிடவும்.",
        "line": "வரி {line}",
        "no_errors": "எந்த பிழையும் கண்டறியப்படவில்லை.",
        "output_unknown": "வெளியீட்டை கணிக்க முடியவில்லை.",
        "generic": "இந்த வரி நிரலின் அடுத்த கட்ட தர்க்கத்தை இயக்குகிறது.",
        "variable": "மாறி கண்டறியப்பட்டது: '{name}' | தரவு வகை: {dtype}. நோக்கம்: மதிப்பை நினைவகத்தில் சேமிக்கிறது. ஏன் பயன்படுத்த வேண்டும்: இதை ஒரு லேபிள் ஒட்டப்பட்ட பெட்டி போல நினைக்கவும். இது நிரலில் பின்னர் மதிப்பை மாற்ற உதவுகிறது.",
        "condition": "முடிவு எடுக்கும் வரி (Condition). நோக்கம்: நிபந்தனை உண்மையா இல்லையா என சரிபார்க்கிறது. ஏன் பயன்படுத்த வேண்டும்: ஒரு சாலை சந்திப்பு போன்றது. நிபந்தனை உண்மையாக இருந்தால் மட்டுமே நிரல் இந்த வழியில் செல்லும்.",
        "loop": "மடக்கு (Loop) வழிமுறை. நோக்கம்: குறியீட்டை மீண்டும் மீண்டும் இயக்குகிறது. ஏன் பயன்படுத்த வேண்டும்: ஒரே குறியீட்டை பல முறை எழுதுவதை தவிர்க்கிறது.",
        "print": "வெளியீடு கட்டளை. நோக்கம்: திரையில் முடிவுகளைக் காட்டுகிறது. ஏன் பயன்படுத்த வேண்டும்: பயனர் நிரலின் முடிவை பார்க்க இது மிகவும் முக்கியம்.",
        "intermediate_suffix": " [இடைநிலை நிலை: இங்கே கட்டுப்பாட்டு ஓட்டம் மாறுவதை கவனிக்கவும்.]",
        "advanced_suffix": " [உயர் நிலை: இங்கே குறியீட்டின் செயல்திறனை மேம்படுத்துவதை கருத்தில் கொள்ளவும்.]"
    }
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                skill_level TEXT DEFAULT 'beginner',
                preferred_language TEXT DEFAULT 'english',
                setup_complete INTEGER DEFAULT 0,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                code TEXT NOT NULL,
                code_language TEXT NOT NULL,
                explanation_language TEXT NOT NULL,
                skill_level TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.execute("""
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
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress_tracking (
                user_id INTEGER PRIMARY KEY,
                programs_analyzed INTEGER DEFAULT 0,
                total_explanations INTEGER DEFAULT 0,
                concepts_learned TEXT DEFAULT '[]',
                concepts_failed TEXT DEFAULT '[]',
                current_level TEXT DEFAULT 'Beginner',
                quiz_accuracy REAL DEFAULT 0.0,
                quizzes_taken INTEGER DEFAULT 0,
                learning_streak INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                rating INTEGER,
                comments TEXT,
                error_reported TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                concept TEXT,
                difficulty TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attention_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                attention_score REAL NOT NULL,
                focus_time INTEGER NOT NULL,
                distracted_time INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view

def current_user():
    if "user_id" not in session: return None
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

def detect_code_language(code, selected="auto"):
    if selected != "auto": return selected
    if re.search(r"#include\s*<|std::|cout\s*<<", code): return "cpp"
    if re.search(r"\bpublic\s+class\b|\bSystem\.out\.println\b", code): return "java"
    if re.search(r"\bfunction\b|console\.log|let\s+|const\s+", code): return "javascript"
    if re.search(r"\bprintf\s*\(|\bscanf\s*\(", code): return "c"
    return "python"

def meaningful_lines(code):
    return [(idx, line.rstrip()) for idx, line in enumerate(code.splitlines(), start=1) if line.strip()]

def concept_map(code):
    return {
        "Variables": bool(re.search(r"(^|\s)(let|const|var|int|float|double|char|String|bool)\s+\w+|\w+\s*=", code)),
        "Input": bool(re.search(r"\b(input|scanf|cin\s*>>|Scanner|readline)\b", code)),
        "Output": bool(re.search(r"\b(print|printf|console\.log|System\.out\.println|cout\s*<<)\b", code)),
        "Loops": bool(re.search(r"\b(for|while|do)\b", code)),
        "Conditions": bool(re.search(r"\b(if|else|elif|switch|case)\b", code)),
        "Functions": bool(re.search(r"\b(def|function)\s+\w+|\w+\s+\w+\s*\([^)]*\)\s*\{", code)),
        "Arrays": bool(re.search(r"\[[^\]]*\]|\b(list|array|vector|ArrayList)\b", code)),
        "Classes": bool(re.search(r"\bclass\s+\w+", code)),
        "Objects": bool(re.search(r"\bnew\s+\w+\s*\(|\.\w+\s*\(", code)),
        "Recursion": False
    }

def explain_lines_intelligent(code, level, lang_key, code_language):
    """Dynamically parses and looks up concept analogy strings in the chosen language."""
    lang_set = TRANSLATIONS.get(lang_key, TRANSLATIONS["english"])
    items = []
    
    for line_number, line in meaningful_lines(code):
        stripped = line.strip()
        kind = "generic"
        details = {"name": "", "dtype": "Data Token"}
        
        # Semicolon/Comment skip
        if stripped.startswith(("#", "//", "/*")):
            items.append({
                "line": line_number,
                "title": lang_set.get("line").format(line=line_number),
                "code": line.strip(),
                "explanation": "Comment Node / Human Note" if lang_key == "english" else "குறிப்பு / टिप्पणी"
            })
            continue

        # Pattern identification matches
        if re.search(r"\b(print|printf|console\.log|System\.out\.println|cout)\b", stripped):
            kind = "print"
        elif re.search(r"\b(for|while)\b", stripped):
            kind = "loop"
        elif re.match(r"^(if|else if|elif|else)\b", stripped):
            kind = "condition"
        else:
            var_match = re.match(r"^(?:(?:int|float|double|char|String|bool|let|const|var)\s+)?([A-Za-z_]\w*)\s*=\s*(.*)$", stripped)
            if var_match and "==" not in stripped:
                kind = "variable"
                details["name"] = var_match.group(1)
                val = var_match.group(2)
                if "int" in stripped or val.isdigit(): details["dtype"] = "Integer (Whole Number)"
                elif "String" in stripped or '"' in val: details["dtype"] = "String (Text)"
                else: details["dtype"] = "Value Node"

        # Construct translated template
        text = lang_set.get(kind, lang_set["generic"]).format(**details)
        if level == "intermediate" and kind != "generic":
            text += lang_set.get("intermediate_suffix", "")
        elif level == "advanced" and kind != "generic":
            text += lang_set.get("advanced_suffix", "")
            
        items.append({
            "line": line_number,
            "title": lang_set.get("line").format(line=line_number),
            "code": line.strip(),
            "explanation": text
        })
    return items

def detect_errors(code, code_language):
    errors = []
    pairs = [("(", ")"), ("[", "]"), ("{", "}")]
    for open_char, close_char in pairs:
        if code.count(open_char) != code.count(close_char):
            errors.append({
                "line": "-",
                "description": f"Unbalanced layout symbols '{open_char}' and '{close_char}' detected.",
                "fix": "Verify all brackets close matching pairs securely."
            })
    return errors if errors else [{"line": "-", "description": "No syntax structural anomalies found.", "fix": "No action required."}]

def separate_complexity(code):
    loop_count = len(re.findall(r"\b(for|while)\b", code))
    return {
        "time": "O(N)" if loop_count > 0 else "O(1)",
        "space": "O(1)",
        "reason": "Evaluated based on structural loop iteration counts processing datasets."
    }

def predict_output(code):
    prints = []
    lines = [line.strip().rstrip(";") for _, line in meaningful_lines(code)]
    for stripped in lines:
        pm = re.search(r"(?:print|System\.out\.println|console\.log)\s*\((.*?)\)", stripped)
        if pm:
            prints.append(pm.group(1).strip().strip("\"'"))
    return "\n".join(prints) if prints else "Pass"

@app.route("/")
def home(): return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db_connection() as conn:
            try:
                cursor = conn.execute("INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                                     (full_name, email, generate_password_hash(password)))
                conn.commit()
                session.clear()
                session["user_id"] = cursor.lastrowid
                session["user_name"] = full_name
                return redirect(url_for("setup"))
            except sqlite3.IntegrityError: flash("Email registration vector already allocated.", "danger")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            return redirect(url_for("dashboard") if user["setup_complete"] else url_for("setup"))
        flash("Invalid validation credentials provided.", "danger")
    return render_template("login.html")

@app.route("/setup", methods=["GET", "POST"])
@login_required
def setup():
    if request.method == "POST":
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET skill_level = ?, preferred_language = ?, setup_complete = 1 WHERE id = ?",
                         (request.form.get("skill_level"), request.form.get("preferred_language"), session["user_id"]))
            conn.commit()
        return redirect(url_for("dashboard"))
    return render_template("setup.html", skill_levels=SKILL_LEVELS, languages=SETUP_LANGUAGES)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    with get_db_connection() as conn:
        history = conn.execute("SELECT * FROM analysis_history WHERE user_id = ? ORDER BY id DESC LIMIT 10", (session["user_id"],)).fetchall()
        favorites = conn.execute("SELECT * FROM saved_explanations WHERE user_id = ? ORDER BY id DESC", (session["user_id"],)).fetchall()
        progress = conn.execute("SELECT * FROM progress_tracking WHERE user_id = ?", (session["user_id"],)).fetchone()
        if not progress:
            conn.execute("INSERT INTO progress_tracking (user_id) VALUES (?)", (session["user_id"],))
            conn.commit()
            progress = conn.execute("SELECT * FROM progress_tracking WHERE user_id = ?", (session["user_id"],)).fetchone()
    return render_template("dashboard.html", user=user, history=history, favorites=favorites, progress=progress,
                           code_languages=CODE_LANGUAGES, explanation_languages=EXPLANATION_LANGUAGES, skill_levels=SKILL_LEVELS,
                           concepts_learned=json.loads(progress["concepts_learned"] or "[]"))

@app.route("/explain-code", methods=["POST"])
@login_required
def explain_code():
    data = request.get_json() or {}
    code = data.get("code", "")
    code_lang = detect_code_language(code, data.get("code_language", "auto"))
    exp_lang = data.get("language", "english")
    skill = data.get("level", "beginner")
    
    concepts = concept_map(code)
    items = explain_lines_intelligent(code, skill, exp_lang, code_lang)
    errors = detect_errors(code, code_lang)
    comp = separate_complexity(code)
    output = predict_output(code)
    
    result = {
        "overview": TRANSLATIONS.get(exp_lang, TRANSLATIONS["english"])["overview"].format(language=code_lang.upper(), lines=len(items)),
        "items": items, "errors": errors, "concepts": concepts, "complexity": comp, "expected_output": output,
        "roadmap": ["Loops Deep Dive", "Functions Blocks Parameter Structures"], "quiz": [],
        "code_language": code_lang, "explanation_language": exp_lang, "skill_level": skill
    }
    
    if code.strip():
        with get_db_connection() as conn:
            cursor = conn.execute("INSERT INTO analysis_history (user_id, title, code, code_language, explanation_language, skill_level, result_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (session["user_id"], code.strip().splitlines()[0][:40], code, code_lang, exp_lang, skill, json.dumps(result)))
            conn.commit()
            result["history_id"] = cursor.lastrowid
    return jsonify(result)

@app.route("/progress-dashboard")
@login_required
def progress_dashboard():
    with get_db_connection() as conn:
        progress = conn.execute("SELECT * FROM progress_tracking WHERE user_id = ?", (session["user_id"],)).fetchone()
    return render_template("progress_dashboard.html", progress=progress)

@app.route("/attention-monitor", methods=["GET", "POST"])
@login_required
def attention_monitor():
    if request.method == "POST":
        data = request.get_json() or {}
        with get_db_connection() as conn:
            conn.execute("INSERT INTO attention_analytics (user_id, attention_score, focus_time, distracted_time) VALUES (?, ?, ?, ?)",
                         (session["user_id"], data.get("score", 100), data.get("focus", 0), data.get("distracted", 0)))
            conn.commit()
        return jsonify({"status": "locked"})
    return render_template("attention_monitor.html")

@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        with get_db_connection() as conn:
            conn.execute("INSERT INTO feedback (user_id, rating, comments) VALUES (?, ?, ?)",
                         (session["user_id"], request.form.get("rating"), request.form.get("comments")))
            conn.commit()
        flash("Feedback successfully saved.", "success")
    return render_template("feedback.html")

@app.route("/favorite/<int:history_id>", methods=["POST"])
@login_required
def favorite(history_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO saved_explanations (user_id, history_id, title) VALUES (?, ?, 'Saved Code Lesson')", (session["user_id"], history_id))
        conn.commit()
    return jsonify({"saved": True})

@app.route("/download/<int:history_id>")
@login_required
def download_pdf(history_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM analysis_history WHERE id = ?", (history_id,)).fetchone()
    res = json.loads(row["result_json"])
    pdf_lines = [f"Language: {row['code_language'].upper()}", f"Level: {row['skill_level'].upper()}", "--- CODE ---", row["code"], "--- EXPLANATION ---"]
    for item in res["items"]: pdf_lines.append(f"{item['title']}: {item['explanation']}")
    return make_response((make_simple_pdf("Lesson Ledger Summary", pdf_lines), 200, {"Content-Type": "application/pdf", "Content-Disposition": f"attachment; filename=session-{history_id}.pdf"}))

def make_simple_pdf(title, lines):
    c = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj"
    f = "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj"
    y = 740
    cmds = ["BT", "/F1 14 Tf", f"50 {y} Td", f"({title}) Tj", "0 -20 Td"]
    for l in lines:
        for chunk in re.findall(".{1,80}", str(l)) or [""]:
            cmds.append(f"({str(chunk).replace('(','\\(').replace(')','\\)')}) Tj\n0 -12 Td")
            y -= 12
            if y < 40: break
    cmds.append("ET")
    stream = "\n".join(cmds)
    co = f"5 0 obj\n<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream\nendobj"
    po = "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj"
    pdf_parts = ["%PDF-1.4", c, po, f, co]
    body = "\n".join(pdf_parts) + "\n"
    offsets = []
    out = bytearray()
    for item in body.splitlines():
        offsets.append(len(out))
        out.extend((item + "\n").encode("utf-8"))
    xref_pos = len(out)
    xt = ["xref", f"0 {len(pdf_parts)}", "0000000000 65535 f "]
    for idx in range(1, len(pdf_parts)): xt.append(f"{offsets[idx]:010d} 00000 n ")
    xt.append(f"trailer\n<< /Size {len(pdf_parts)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF")
    out.extend(("\n".join(xt)).encode("utf-8"))
    return bytes(out)

init_db()
if __name__ == "__main__": app.run(debug=True)
