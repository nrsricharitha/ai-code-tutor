import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ai_code_tutor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    skill_level = db.Column(db.String(20), default='Beginner')
    preferred_language = db.Column(db.String(20), default='English')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    history = db.relationship('AnalysisHistory', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AnalysisHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code_content = db.Column(db.Text, nullable=False)
    programming_language = db.Column(db.String(20))
    explanation = db.Column(db.Text)
    concepts_detected = db.Column(db.String(200)) # JSON string
    complexity_score = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    history_id = db.Column(db.Integer, db.ForeignKey('analysis_history.id'), nullable=False)
    title = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    programs_analyzed = db.Column(db.Integer, default=0)
    concepts_learned = db.Column(db.Integer, default=0)
    total_explanations = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or Email already exists')
            return redirect(url_for('signup'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # Initialize progress
        progress = Progress(user_id=new_user.id)
        db.session.add(progress)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('profile_setup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile-setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    if request.method == 'POST':
        current_user.skill_level = request.form.get('skill_level')
        current_user.preferred_language = request.form.get('preferred_language')
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('profile_setup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    history = AnalysisHistory.query.filter_by(user_id=current_user.id).order_by(AnalysisHistory.created_at.desc()).limit(10).all()
    return render_template('dashboard.html', history=history)

@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze_code():
    data = request.json
    code = data.get('code')
    prog_lang = data.get('language')
    explanation_lang = data.get('explanation_language', current_user.preferred_language)
    skill_level = data.get('skill_level', current_user.skill_level)

    # In a real scenario, we'd call OpenAI here. 
    # For now, we'll create a helper function to simulate or call the AI.
    analysis_result = perform_ai_analysis(code, prog_lang, explanation_lang, skill_level)
    
    # Save to history
    history = AnalysisHistory(
        user_id=current_user.id,
        code_content=code,
        programming_language=prog_lang,
        explanation=analysis_result['explanation'],
        concepts_detected=analysis_result['concepts'],
        complexity_score=analysis_result['complexity_score']
    )
    db.session.add(history)
    
    # Update progress
    progress = Progress.query.filter_by(user_id=current_user.id).first()
    if progress:
        progress.programs_analyzed += 1
        progress.total_explanations += 1
        # Simple logic for concepts learned: count unique concepts in this analysis
        # (This is simplified for the demo)
        progress.concepts_learned += len(analysis_result['concepts'].split(','))
    
    db.session.commit()
    
    return jsonify({
        'id': history.id,
        'explanation': analysis_result['explanation'],
        'concepts': analysis_result['concepts'],
        'complexity': analysis_result['complexity_score'],
        'errors': analysis_result['errors'],
        'output_prediction': analysis_result['output_prediction'],
        'quiz': analysis_result['quiz'],
        'roadmap': analysis_result['roadmap']
    })

@app.route('/api/favorites/add', methods=['POST'])
@login_required
def add_favorite():
    data = request.json
    history_id = data.get('history_id')
    title = data.get('title', 'Saved Explanation')
    
    fav = Favorite(user_id=current_user.id, history_id=history_id, title=title)
    db.session.add(fav)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/history')
@login_required
def get_history():
    history = AnalysisHistory.query.filter_by(user_id=current_user.id).order_by(AnalysisHistory.created_at.desc()).all()
    return jsonify([{
        'id': h.id,
        'code': h.code_content,
        'lang': h.programming_language,
        'date': h.created_at.strftime('%Y-%m-%d %H:%M')
    } for h in history])

def perform_ai_analysis(code, prog_lang, explanation_lang, skill_level):
    from openai import OpenAI
    client = OpenAI() # Uses pre-configured sandbox environment
    
    prompt = f"""
    Analyze the following {prog_lang} code for a {skill_level} student.
    Provide the response in {explanation_lang}.
    
    Code:
    {code}
    
    Return a JSON object with:
    1. "explanation": A line-by-line beginner-friendly explanation.
    2. "concepts": A comma-separated list of programming concepts detected (e.g., Loops, Variables).
    3. "complexity_score": An integer from 1 to 10.
    4. "errors": A list of objects with "description", "fix", and "line".
    5. "output_prediction": The expected output of the code.
    6. "quiz": A list of 3-5 multiple choice questions about the code.
    7. "roadmap": A list of 3 topics to learn next.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an expert programming tutor."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # Fallback if AI fails
        return {
            "explanation": "Could not generate explanation at this time.",
            "concepts": "Unknown",
            "complexity_score": 0,
            "errors": [],
            "output_prediction": "N/A",
            "quiz": [],
            "roadmap": []
        }

@app.route('/api/progress')
@login_required
def get_progress():
    p = Progress.query.filter_by(user_id=current_user.id).first()
    if not p:
        return jsonify({})
    return jsonify({
        'programs_analyzed': p.programs_analyzed,
        'concepts_learned': p.concepts_learned,
        'total_explanations': p.total_explanations,
        'skill_level': current_user.skill_level
    })

@app.route('/api/export-pdf', methods=['POST'])
@login_required
def export_pdf():
    from fpdf import FPDF
    data = request.json
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="AI Code Tutor - Analysis Report", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"User: {current_user.username}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Code:", ln=True)
    pdf.set_font("Courier", size=10)
    pdf.multi_cell(0, 5, txt=data.get('code', ''))
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Explanation:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 5, txt=data.get('explanation', ''))
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Quiz:", ln=True)
    pdf.set_font("Arial", size=11)
    for i, q in enumerate(data.get('quiz', []), 1):
        pdf.multi_cell(0, 5, txt=f"Q{i}: {q.get('question', '')}")
        pdf.ln(2)

    # Save to a temporary file
    output_path = f"/tmp/report_{current_user.id}.pdf"
    pdf.output(output_path)
    
    from flask import send_file
    return send_file(output_path, as_attachment=True, download_name="ai_code_tutor_report.pdf")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
