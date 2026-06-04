# AI Code Tutor

A complete web application built with Flask, SQLite, and AI to help students understand programming code in simple language and multiple Indian languages.

## Features

- **Multilingual Code Explanation**: Supports English, Telugu, Hindi, Marathi, Kannada, and Tamil.
- **Error Detection**: Identifies syntax issues and suggests fixes.
- **Output Prediction**: Predicts the expected result of code execution.
- **Quiz Generation**: Automatically creates quizzes based on the code.
- **Learning Roadmap**: Suggests topics to learn next.
- **Progress Tracking**: Visualizes learning statistics.
- **Modern UI**: Glassmorphism design with Dark/Light mode.
- **PDF Export**: Download analysis reports as PDF.

## Tech Stack

- **Backend**: Flask (Python), SQLite
- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript
- **AI Integration**: OpenAI GPT-4o
- **PDF Generation**: fpdf2

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd ai_code_tutor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file based on `.env.example`:
   ```env
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///instance/ai_code_tutor.db
   OPENAI_API_KEY=your_openai_api_key
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000`.

## Deployment

This project is ready for deployment on **Render**.
- Use the provided `render.yaml` for automated setup.
- Ensure the `OPENAI_API_KEY` is set in the environment variables on Render.

## Project Structure

```
ai_code_tutor/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── render.yaml         # Deployment configuration
├── static/
│   ├── css/style.css   # Styling with Glassmorphism
│   └── js/main.js      # Frontend logic
├── templates/          # HTML templates
│   ├── base.html
│   ├── landing.html
│   ├── login.html
│   ├── signup.html
│   ├── profile_setup.html
│   └── dashboard.html
└── instance/           # Database storage
```
