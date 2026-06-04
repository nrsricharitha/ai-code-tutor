document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle
    const themeToggle = document.getElementById('dark-mode-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('change', () => {
            document.body.classList.toggle('dark-mode');
        });
    }

    // Navigation
    const navItems = ['nav-editor', 'nav-history', 'nav-favorites', 'nav-progress'];
    const sections = ['editor-section', 'history-section', 'favorites-section', 'progress-section'];

    navItems.forEach((id, index) => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                navItems.forEach(navId => document.getElementById(navId)?.classList.remove('active'));
                sections.forEach(secId => document.getElementById(secId)?.classList.add('hidden'));
                
                el.classList.add('active');
                document.getElementById(sections[index]).classList.remove('hidden');

                if (id === 'nav-progress') loadProgress();
                if (id === 'nav-history') loadHistory();
            });
        }
    });

    // Code Explanation
    const explainBtn = document.getElementById('explain-btn');
    if (explainBtn) {
        explainBtn.addEventListener('click', async () => {
            const code = document.getElementById('code-editor').value;
            const language = document.getElementById('prog-language').value;
            const explanationLang = document.getElementById('explanation-language').value;

            if (!code.trim()) {
                alert('Please paste some code first!');
                return;
            }

            showLoader(true);
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        language: language,
                        explanation_language: explanationLang
                    })
                });

                const result = await response.json();
                displayResults(result);
            } catch (error) {
                console.error('Error:', error);
                alert('Something went wrong during analysis.');
            } finally {
                showLoader(false);
            }
        });
    }

    // Clear Editor
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            document.getElementById('code-editor').value = '';
            document.getElementById('analysis-results').classList.add('hidden');
        });
    }

    // PDF Export
    const exportBtn = document.getElementById('export-pdf-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            const code = document.getElementById('code-editor').value;
            const explanation = document.getElementById('explanation-content').innerText;
            // Simplified quiz data for export
            const quiz = Array.from(document.querySelectorAll('.quiz-item')).map(q => ({
                question: q.querySelector('p').innerText
            }));

            const response = await fetch('/api/export-pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, explanation, quiz })
            });

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ai_code_tutor_report.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
        });
    }
});

function showLoader(show) {
    document.getElementById('loader').classList.toggle('hidden', !show);
}

function displayResults(data) {
    document.getElementById('analysis-results').classList.remove('hidden');
    
    // Explanation
    document.getElementById('explanation-content').innerHTML = data.explanation.replace(/\n/g, '<br>');
    
    // Concepts
    const conceptsList = document.getElementById('concepts-list');
    conceptsList.innerHTML = '';
    data.concepts.split(',').forEach(concept => {
        const span = document.createElement('span');
        span.className = 'badge';
        span.innerHTML = `<i class="fas fa-check"></i> ${concept.trim()}`;
        conceptsList.appendChild(span);
    });

    // Complexity
    const complexityFill = document.getElementById('complexity-fill');
    const complexityText = document.getElementById('complexity-text');
    const score = data.complexity || 0;
    complexityFill.style.width = `${score * 10}%`;
    complexityFill.style.height = '100%';
    complexityFill.style.background = score < 4 ? '#22c55e' : (score < 7 ? '#f59e0b' : '#ef4444');
    complexityText.innerText = `${score}/10 (${score < 4 ? 'Beginner' : (score < 7 ? 'Intermediate' : 'Advanced')})`;

    // Output Prediction
    document.getElementById('output-prediction').innerText = data.output_prediction;

    // Errors
    const errorsList = document.getElementById('errors-list');
    errorsList.innerHTML = '';
    if (data.errors && data.errors.length > 0) {
        data.errors.forEach(err => {
            const div = document.createElement('div');
            div.className = 'error-item';
            div.innerHTML = `<strong>Line ${err.line}:</strong> ${err.description}<br><small>Fix: ${err.fix}</small>`;
            errorsList.appendChild(div);
        });
    } else {
        errorsList.innerHTML = '<p class="success-text"><i class="fas fa-check-circle"></i> No syntax errors detected!</p>';
    }

    // Quiz
    const quizContainer = document.getElementById('quiz-container');
    quizContainer.innerHTML = '';
    data.quiz.forEach((q, i) => {
        const div = document.createElement('div');
        div.className = 'quiz-item';
        div.innerHTML = `<p><strong>Q${i+1}:</strong> ${q.question}</p>`;
        quizContainer.appendChild(div);
    });

    // Roadmap
    const roadmapList = document.getElementById('roadmap-list');
    roadmapList.innerHTML = '';
    data.roadmap.forEach(topic => {
        const li = document.createElement('li');
        li.innerText = topic;
        roadmapList.appendChild(li);
    });

    // Scroll to results
    document.getElementById('analysis-results').scrollIntoView({ behavior: 'smooth' });
}

async function loadProgress() {
    const response = await fetch('/api/progress');
    const data = await response.json();
    document.getElementById('stat-analyzed').innerText = data.programs_analyzed || 0;
    document.getElementById('stat-concepts').innerText = data.concepts_learned || 0;
    document.getElementById('stat-explanations').innerText = data.total_explanations || 0;
}

async function loadHistory() {
    const response = await fetch('/api/history');
    const data = await response.json();
    const list = document.getElementById('history-list');
    list.innerHTML = '';
    data.forEach(item => {
        const card = document.createElement('div');
        card.className = 'history-card glass';
        card.innerHTML = `
            <h4>${item.lang.toUpperCase()} Code</h4>
            <p>${item.date}</p>
            <pre>${item.code.substring(0, 50)}...</pre>
            <button class="btn btn-small" onclick="viewHistoryItem(${item.id})">View Full</button>
        `;
        list.appendChild(card);
    });
}
