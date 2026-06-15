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

CONCEPTS = [
    "Variables", "Input", "Output", "Loops", "Conditions",
    "Functions", "Arrays", "Classes", "Objects", "Recursion"
]

TRANSLATIONS = {
    "english": {
        "overview": "{language} code with {lines} lines. It focuses on: {concepts}.",
        "overview_empty": "Provide a code snippet to begin lesson visualization.",
        "line": "Line {line}",
        "no_errors": "No obvious syntax structural flaws were found in this line segment.",
        "output_unknown": "Execution path cannot be reliably inferred dynamically.",
    },
    "telugu": {
        "overview": "{language} కోడ్ {lines} లైన్లు కలిగి ఉంది. ముఖ్యమైన అంశాలు: {concepts}.",
        "overview_empty": "పాఠాన్ని ప్రారంభించడానికి కోడ్ ముక్కను అందించండి.",
        "line": "లైన్ {line}",
        "no_errors": "నిర్మాణాత్మక లోపాలు ఏవీ కనుగొనబడలేదు.",
        "output_unknown": "అవుట్‌పుట్‌ను అంచనా వేయడం సాధ్యం కాలేదు.",
    },
    "hindi": {
        "overview": "{language} कोड में {lines} लाइनें हैं। मुख्य विषय: {concepts}.",
        "overview_empty": "पाठ शुरू करने के लिए कोड डालें।",
        "line": "लाइन {line}",
        "no_errors": "कोई स्पष्ट संरचनात्मक त्रुटि नहीं मिली।",
        "output_unknown": "आउटपुट का अनुमान नहीं लगाया जा सकता।",
    },
    "marathi": {
        "overview": "{language} कोडमध्ये {lines} ओळी आहेत. मुख्य संकल्पना: {concepts}.",
        "overview_empty": "धडा सुरू करण्यासाठी कोड प्रविष्ट करा.",
        "line": "ओळ {line}",
        "no_errors": "कोणतीही त्रुटी आढळली नाही.",
        "output_unknown": "आउटपुटचा अंदाज लावता येत नाही.",
    },
    "kannada": {
        "overview": "{language} ಕೋಡ್ {lines} ಸಾಲುಗಳನ್ನು ಹೊಂದಿದೆ. ಪ್ರಮುಖ ಪರಿಕಲ್ಪನೆಗಳು: {concepts}.",
        "overview_empty": "ಪಾಠವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಕೋಡ್ ನಮೂದಿಸಿ.",
        "line": "ಸಾಲು {line}",
        "no_errors": "ಯಾವುದೇ ದೋಷ ಕಂಡುಬಂದಿಲ್ಲ.",
        "output_unknown": "ಔಟ್‌ಪುಟ್ ಊಹಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
    },
    "tamil": {
        "overview": "{language} குறியீடு {lines} வரிகளைக் கொண்டுள்ளது. முக்கிய கருத்துக்கள்: {concepts}.",
        "overview_empty": "பாடத்தைத் தொடங்க குறியீட்டை உள்ளிடவும்.",
        "line": "வரி {line}",
        "no_errors": "எந்த பிழையும் கண்டறியப்படவில்லை.",
        "output_unknown": "வெளியீட்டை கணிக்க முடியவில்லை.",
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS classroom_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                code_snippet TEXT,
                instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS classroom_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                quiz_score INTEGER,
                quiz_total INTEGER,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    if "user_id" not in session:
        return None
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

def process_teacher_explanation(line, language, mode):
    """Parses individual semantic structures to act like a teacher rather than a generic machine translator."""
    stripped = line.strip()
    explanation = "This line moves our program's structural workflow sequence forward."
    
    # 1. Look for Variables & Data Types
    var_match = re.match(r"^(?:(?:int|float|double|char|String|bool|let|const|var)\s+)?([A-Za-z_]\w*)\s*=\s*(.*)$", stripped)
    if var_match and "==" not in stripped:
        name = var_match.group(1)
        val = var_match.group(2)
        dtype = "Inferred Data Component"
        if "int" in stripped or val.isdigit(): dtype = "Integer (Whole Number)"
        elif "float" in stripped or "double" in stripped or "." in val: dtype = "Floating-Point (Decimal Number)"
        elif "String" in stripped or '"' in val or "'" in val: dtype = "String (Text Collection)"
        
        if mode == "beginner":
            explanation = f"Variable Detected: '{name}' | Data Type Type: {dtype}. Purpose: Stores the value ({val}) inside memory workspace. Why Used: Think of this like a labeled storage box. It allows our program to access or change this value later by simply calling its name."
        elif mode == "intermediate":
            explanation = f"Allocation Frame: Assigned token '{name}' as a {dtype} referencing entity node value '{val}'. This registers the storage token inside the active context scope table for operational access blocks."
        else:
            explanation = f"Memory Allocation / Pointer Assignment: Bound visual token '{name}' maps to explicit data type block {dtype} wrapping payload expression '{val}'. Optimizes register usage by preventing repetitive raw evaluation metrics."
        return explanation

    # 2. Look for Conditional Branches
    if re.match(r"^(if|else if|elif)\b", stripped):
        if mode == "beginner":
            explanation = "Decision Node Detected. Purpose: Checks a true/false condition statement. Why Used: Works just like a crossroad analogy. If the condition is true, the program takes this path; otherwise, it skips it entirely or goes to the next branch."
        else:
            explanation = "Conditional evaluation boundary fork. Checks Boolean criteria vector to modify standard code execution stream paths dynamically."
        return explanation

    # 3. Look for Loop Blocks
    if re.search(r"\b(for|while)\b", stripped):
        if mode == "beginner":
            explanation = "Loop Repetition Mechanism. Purpose: Repeatedly runs a block of code commands. Why Used: Saves you from writing the exact same lines of code over and over again. It will run until its ending rule or boundary condition finishes."
        else:
            explanation = "Iterative sequence counter boundary loop. Increments contextual runtime registers until block boundary constraints evaluate to false."
        return explanation

    # 4. Look for Outputs
    if re.search(r"\b(print|printf|console\.log|System\.out\.println|cout)\b", stripped):
        explanation = "Output Command. Purpose: Displays text data or variable values directly onto the user screen. Why Used: Essential for communication. Without this, your program's results would stay hidden inside your computer's memory chip where nobody could see them."
        return explanation
        
    return explanation

def explain_lines_intelligent(code, level, explanation_language, code_language):
    phrases = TRANSLATIONS.get(explanation_language, TRANSLATIONS["english"])
    items = []
    for line_number, line in meaningful_lines(code):
        text = process_teacher_explanation(line, code_language, level)
        items.append({
            "line": line_number,
            "title": phrases.get("line", "Line {line}").format(line=line_number),
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
                "fix": f"Verify all brackets close matching pairs securely."
            })
    for num, line in meaningful_lines(code):
        st = line.strip()
        if code_language == "python" and re.match(r"^(if|elif|else|for|while|def|class)\b", st) and not st.endswith(":"):
            errors.append({
                "line": num,
                "description": "Python compound statement missing syntax delimiter colon (':').",
                "fix": "Append a ':' symbol directly to the end of this statement path."
            })
        elif code_language in {"c", "cpp", "java", "javascript"}:
            if st and not st.endswith((";", "{", "}", ":", ",")) and not re.match(r"^(if|for|while|else|switch|class|function)\b", st):
                errors.append({
                    "line": num,
                    "description": "Missing horizontal expression delimiter terminator statement semicolon (';').",
                    "fix": "Add a ';' at the end of the line segment."
                })
    return errors if errors else [{"line": "-", "description": "No syntax structural anomalies found.", "fix": "No action required."}]

def separate_complexity(code):
    loop_count = len(re.findall(r"\b(for|while)\b", code))
    nesting = max((len(line) - len(line.lstrip(" "))) // 4 for _, line in meaningful_lines(code)) if code.strip() else 0
    
    if loop_count == 0:
        time_comp, space_comp = "O(1)", "O(1)"
        reason = "Runs sequentially line-by-line without allocation loops or expansion buffers."
    elif loop_count == 1:
        time_comp, space_comp = "O(N)", "O(1)"
        reason = "Contains a single iteration path processing element datasets cleanly."
    elif nesting >= 2 or loop_count > 1:
        time_comp, space_comp = "O(N^2)", "O(1)"
        reason = "Nested iteration loops process structures quadratically relative to metrics scale data variables."
    else:
        time_comp, space_comp = "O(N)", "O(1)"
        reason = "Standard continuous linear workspace processing logic."
        
    return {"time": time_comp, "space": space_comp, "reason": reason}

def predict_output(code):
    prints = []
    variables = {}
    lines = [line.strip().rstrip(";") for _, line in meaningful_lines(code)]
    for stripped in lines:
        assign = re.match(r"^(?:(?:let|const|var|int|float|String)\s+)?([A-Za-z_]\w*)\s*=\s*(.*)$", stripped)
        if assign:
            try: variables[assign.group(1)] = int(assign.group(2))
            except ValueError: variables[assign.group(1)] = assign.group(2).strip("\"'")
        pm = re.search(r"(?:print|System\.out\.println|console\.log)\s*\((.*?)\)", stripped)
        if pm:
            val = pm.group(1).strip().strip("\"'")
            prints.append(str(variables.get(val, val)))
    return "\n".join(prints) if prints else "Pass (Execution successfully processed without console footprint tracking)"

def generate_dynamic_quiz(concepts, level):
    questions = []
    if concepts.get("Loops"):
        questions.append({
            "type": "MCQ",
            "question": "Which programming token sequence forces an ongoing iterative conditional loop to loop cleanly?",
            "options": ["while", "switch", "def", "import"],
            "answer": 0
        })
    if concepts.get("Variables"):
        questions.append({
            "type": "TF",
            "question": "Variables serve as permanent hardware address pins that cannot reassign numerical bounds.",
            "options": ["True", "False"],
            "answer": 1
        })
    if not questions:
        questions.append({
            "type": "MCQ",
            "question": "What structural tracking property determines top-down software sequence execution lines?",
            "options": ["Control Flow Engine", "Compilation Register", "Linking Map", "Bitwise Core"],
            "answer": 0
        })
    return questions

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        with get_db_connection() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    (full_name, email, generate_password_hash(password), role)
                )
                conn.commit()
                session.clear()
                session["user_id"] = cursor.lastrowid
                session["user_name"] = full_name
                session["role"] = role
                return redirect(url_for("setup"))
            except sqlite3.IntegrityError:
                flash("Email registration vector already allocated.", "danger")
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
            session["role"] = user["role"]
            return redirect(url_for("dashboard") if user["setup_complete"] else url_for("setup"))
        flash("Invalid validation credentials provided.", "danger")
    return render_template("login.html")

@app.route("/setup", methods=["GET", "POST"])
@login_required
def setup():
    if request.method == "POST":
        skill_level = request.form.get("skill_level", "beginner")
        preferred_language = request.form.get("preferred_language", "english")
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE users SET skill_level = ?, preferred_language = ?, setup_complete = 1 WHERE id = ?",
                (skill_level, preferred_language, session["user_id"])
            )
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
    history, favorites, progress = dashboard_data_extended(session["user_id"])
    return render_template(
        "dashboard.html", user=user, history=history, favorites=favorites,
        progress=progress, code_languages=CODE_LANGUAGES, explanation_languages=EXPLANATION_LANGUAGES,
        skill_levels=SKILL_LEVELS, concepts_learned=json.loads(progress["concepts_learned"])
    )

def dashboard_data_extended(user_id):
    with get_db_connection() as conn:
        history = conn.execute("SELECT * FROM analysis_history WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,)).fetchall()
        favorites = conn.execute("SELECT * FROM saved_explanations WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
        progress = conn.execute("SELECT * FROM progress_tracking WHERE user_id = ?", (user_id,)).fetchone()
        if not progress:
            conn.execute("INSERT INTO progress_tracking (user_id, concepts_learned, concepts_failed) VALUES (?, '[]', '[]')", (user_id,))
            conn.commit()
            progress = conn.execute("SELECT * FROM progress_tracking WHERE user_id = ?", (user_id,)).fetchone()
    return history, favorites, progress

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
    
    # Roadmap items transformation calculation matrix
    roadmap_items = ["Functions Integration Pipeline", "Dataset Mapping Tracking Arrays"] if concepts["Variables"] else ["Fundamental Memory Variables Syntax"]
    quiz_items = generate_dynamic_quiz(concepts, skill)
    
    result = {
        "overview": f"Processed {code_lang.upper()} architectural segment containing {len(items)} instructional block nodes.",
        "items": items, "errors": errors, "concepts": concepts, "complexity": comp,
        "expected_output": output, "roadmap": roadmap_items, "quiz": quiz_items,
        "code_language": code_lang, "explanation_language": exp_lang, "skill_level": skill
    }
    
    if code.strip():
        history_id = store_history(session["user_id"], code, code_lang, exp_lang, skill, result)
        result["history_id"] = history_id
        update_progress_matrix(session["user_id"], concepts, errors)
    return jsonify(result)

def store_history(uid, code, clang, elang, skill, res):
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO analysis_history (user_id, title, code, code_language, explanation_language, skill_level, result_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, code.strip().splitlines()[0][:40] if code.strip() else "Code Block", code, clang, elang, skill, json.dumps(res))
        )
        conn.commit()
        return cursor.lastrowid

def update_progress_matrix(uid, concepts, errors):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM progress_tracking WHERE user_id = ?", (uid,)).fetchone()
        learned = set(json.loads(row["concepts_learned"]))
        failed = set(json.loads(row["concepts_failed"]))
        
        for k, v in concepts.items():
            if v:
                if any(e["line"] != "-" for e in errors): failed.add(k)
                else:
                    learned.add(k)
                    failed.discard(k)
                    
        conn.execute(
            "UPDATE progress_tracking SET programs_analyzed = programs_analyzed + 1, total_explanations = total_explanations + 1, concepts_learned = ?, concepts_failed = ? WHERE user_id = ?",
            (json.dumps(list(learned)), json.dumps(list(failed)), uid)
        )
        conn.commit()

# --- TARGET INTERACTIVE ROUTE ENDPOINTS FOR TABS ---
@app.route("/learning-path")
@login_required
def learning_path():
    _, _, progress = dashboard_data_extended(session["user_id"])
    return render_template("learning_path.html", progress=progress, learned=json.loads(progress["concepts_learned"]))

@app.route("/weakness-analysis")
@login_required
def weakness_analysis():
    _, _, progress = dashboard_data_extended(session["user_id"])
    return render_template("weakness_analysis.html", progress=progress, failed=json.loads(progress["concepts_failed"]))

@app.route("/progress-dashboard")
@login_required
def progress_dashboard():
    user = current_user()
    _, _, progress = dashboard_data_extended(session["user_id"])
    return render_template("progress_dashboard.html", user=user, progress=progress)

@app.route("/adaptive-quiz", methods=["GET", "POST"])
@login_required
def adaptive_quiz():
    if request.method == "POST":
        data = request.get_json() or {}
        with get_db_connection() as conn:
            conn.execute("INSERT INTO quiz_results (user_id, score, total, concept) VALUES (?, ?, ?, 'General Check')",
                         (session["user_id"], data.get("score"), data.get("total")))
            conn.execute("UPDATE progress_tracking SET quizzes_taken = quizzes_taken + 1 WHERE user_id = ?", (session["user_id"],))
            conn.commit()
        return jsonify({"status": "Quiz score locked dynamically"})
    return render_template("adaptive_quiz.html")

@app.route("/classroom", methods=["GET", "POST"])
@login_required
def classroom():
    user = current_user()
    with get_db_connection() as conn:
        if request.method == "POST" and user["role"] == "teacher":
            conn.execute("INSERT INTO classroom_assignments (teacher_id, title, instructions) VALUES (?, ?, ?)",
                         (session["user_id"], request.form.get("title"), request.form.get("instructions")))
            conn.commit()
        assignments = conn.execute("SELECT * FROM classroom_assignments ORDER BY id DESC").fetchall()
    return render_template("classroom.html", user=user, assignments=assignments)

@app.route("/attention-monitor", methods=["GET", "POST"])
@login_required
def attention_monitor():
    if request.method == "POST":
        data = request.get_json() or {}
        with get_db_connection() as conn:
            conn.execute("INSERT INTO attention_analytics (user_id, attention_score, focus_time, distracted_time) VALUES (?, ?, ?, ?)",
                         (session["user_id"], data.get("score"), data.get("focus"), data.get("distracted")))
            conn.commit()
        return jsonify({"status": "Metrics registered"})
    return render_template("attention_monitor.html")

@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        with get_db_connection() as conn:
            conn.execute("INSERT INTO feedback (user_id, rating, comments) VALUES (?, ?, ?)",
                         (session["user_id"], request.form.get("rating"), request.form.get("comments")))
            conn.commit()
        flash("Feedback shared successfully.", "success")
    return render_template("feedback.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html", user=current_user())

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        session["reset_email"] = request.form.get("email")
        return redirect(url_for("reset_password"))
    return render_template("forgot_password.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE email = ?",
                         (generate_password_hash(request.form.get("password")), session.get("reset_email")))
            conn.commit()
        return redirect(url_for("login"))
    return render_template("reset_password.html")

@app.route("/favorite/<int:history_id>", methods=["POST"])
@login_required
def favorite(history_id):
    with get_db_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO saved_explanations (user_id, history_id, title) VALUES (?, ?, 'Saved Code Block')",
                     (session["user_id"], history_id))
        conn.commit()
    return jsonify({"saved": True})

@app.route("/download/<int:history_id>")
@login_required
def download_pdf(history_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM analysis_history WHERE id = ?", (history_id,)).fetchone()
    res = json.loads(row["result_json"])
    pdf_lines = [
        f"Language Segment: {row['code_language'].upper()}",
        f"Pedagogical Tracking Mode: {row['skill_level'].upper()}",
        "--- SOURCE TARGET CODE ---",
        row["code"],
        "--- INTERPRETIVE ANALYSIS MATRIX ---",
        res["overview"],
        "--- LINE EXPLANATION FRAMEWORK ---"
    ]
    for item in res["items"]:
        pdf_lines.append(f"{item['title']}: {item['explanation']}")
    pdf_lines.extend([
        "--- STRUCTURAL PERFORMANCE DATA ---",
        f"Time Profile Complexity: {res['complexity']['time']}",
        f"Space allocation profile footprint: {res['complexity']['space']}"
    ])
    return make_response((make_simple_pdf("Pedagogical Synthesis Ledger", pdf_lines), 200, {
        "Content-Type": "application/pdf",
        "Content-Disposition": f"attachment; filename=tutor-session-{history_id}.pdf"
    }))

def pdf_escape(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def make_simple_pdf(title, lines):
    catalog_obj = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj"
    pages_obj = "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj"
    font_obj = "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj"
    y = 740
    commands = ["BT", "/F1 14 Tf", f"50 {y} Td", f"({pdf_escape(title)}) Tj", "0 -20 Td"]
    for l in lines:
        for chunk in re.findall(".{1,80}", str(l)) or [""]:
            commands.append(f"({pdf_escape(chunk)}) Tj")
            commands.append("0 -12 Td")
            y -= 12
            if y < 40: break
        if y < 40: break
    commands.append("ET")
    st_content = "\n".join(commands)
    content_obj = f"5 0 obj\n<< /Length {len(st_content.encode('utf-8'))} >>\nstream\n{st_content}\nendstream\nendobj"
    page_obj = "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj"
    pdf_parts = ["%PDF-1.4", catalog_obj, pages_obj, page_obj, font_obj, content_obj]
    body = "\n".join(pdf_parts) + "\n"
    offsets = []
    pdf_out = bytearray()
    for item in body.splitlines():
        offsets.append(len(pdf_out))
        pdf_out.extend((item + "\n").encode("utf-8"))
    xref_pos = len(pdf_out)
    xref_table = ["xref", f"0 {len(pdf_parts)}", "0000000000 65535 f "]
    for idx in range(1, len(pdf_parts)):
        xref_table.append(f"{offsets[idx]:010d} 00000 n ")
    xref_table.append(f"trailer\n<< /Size {len(pdf_parts)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF")
    pdf_out.extend(("\n".join(xref_table)).encode("utf-8"))
    return bytes(pdf_out)

init_db()

if __name__ == "__main__":
    app.run(debug=True)
