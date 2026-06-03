const examples = [
    {
        title: "Python Loop",
        code: `for i in range(3):
    print("Hello")`
    },
    {
        title: "JavaScript Function",
        code: `function add(a, b) {
    return a + b;
}
console.log("Done");`
    },
    {
        title: "Java Class",
        code: `class Student {
    public static void main(String[] args) {
        System.out.println("Welcome");
    }
}`
    }
];

let lastExplanationData = null;
let currentHistoryId = null;

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function languagesForPreference(preference, data) {
    const allLanguages = data?.supported_languages || ["English", "Telugu", "Hindi", "Marathi", "Kannada", "Tamil"];
    if (preference === "Multiple Languages") {
        return allLanguages;
    }
    return allLanguages.includes(preference) ? [preference] : ["English"];
}

function renderProgress(progress) {
    if (!progress) {
        return;
    }
    document.querySelector("#programCount").textContent = progress.programs_analyzed;
    document.querySelector("#explanationCount").textContent = progress.total_explanations;
    document.querySelector("#conceptCount").textContent = progress.concepts_learned.length;
    document.querySelector("#currentLevel").textContent = progress.current_level;
    const fill = document.querySelector("#progressFill");
    fill.style.width = `${Math.min(progress.concepts_learned.length * 12.5, 100)}%`;
}

function renderExplanation(data) {
    const output = document.querySelector("#outputContent");
    const badge = document.querySelector("#detectedLanguage");
    const preference = document.querySelector("#languagePreference").value;
    const languages = languagesForPreference(preference, data);

    lastExplanationData = data;
    currentHistoryId = data.history_id || currentHistoryId;
    badge.textContent = data.language;
    renderProgress(data.progress);

    const summaryHtml = languages.map((language) => `
        <p><strong class="language-label">${language}:</strong> ${data.summaries[language]}</p>
    `).join("");

    const lineHtml = data.lines.map((line) => {
        const explanations = languages.map((language) => `
            <p><strong class="language-label">${language}:</strong> ${line.explanations[language]}</p>
        `).join("");
        const problem = data.errors.find((error) => error.line === line.number);
        return `
            <article class="line-card ${problem ? "problem-line" : ""}">
                <div class="line-code">
                    <span>Line ${line.number}</span>
                    <code>${escapeHtml(line.code || "blank line")}</code>
                </div>
                <div>${explanations}</div>
                ${problem ? `<p class="problem-note">${problem.title}: ${problem.fix}</p>` : ""}
            </article>
        `;
    }).join("");

    const conceptHtml = ["variable", "loop", "condition", "function", "array", "class", "object", "recursion"].map((concept) => `
        <span class="concept-pill ${data.concepts.includes(concept) ? "active" : ""}">✓ ${concept}</span>
    `).join("");

    const errorHtml = data.errors.length
        ? data.errors.map((error) => `<li>${error.line ? `Line ${error.line}: ` : ""}${error.message} ${error.fix}</li>`).join("")
        : "<li>No common syntax mistakes detected.</li>";

    output.className = "explanation-content switching-language";
    output.innerHTML = `
        <div class="summary-card">
            <div class="result-actions">
                <button class="secondary-button" id="favoriteBtn" type="button">Save Favorite</button>
                <button class="secondary-button" id="downloadPdfBtn" type="button">Download PDF</button>
            </div>
            <h3>Summary</h3>
            ${summaryHtml}
            <h3>Concepts Detected</h3>
            <div class="concept-grid">${conceptHtml}</div>
            <h3>Complexity</h3>
            <p>Complexity Level: <strong>${data.complexity.level} (${data.complexity.score}/10)</strong></p>
            <h3>Expected Output</h3>
            <pre class="output-preview">${escapeHtml(data.expected_output)}</pre>
        </div>
        <div class="summary-card">
            <h3>Error Check</h3>
            <ul>${errorHtml}</ul>
        </div>
        ${lineHtml}
        <div class="summary-card">
            <h3>Next Topics</h3>
            <ul>${data.roadmap.map((topic) => `<li>${topic}</li>`).join("")}</ul>
            <h3>Quiz</h3>
            <ol>${data.quiz.map((question) => `<li>${question}</li>`).join("")}</ol>
        </div>
    `;

    document.querySelector("#favoriteBtn").addEventListener("click", toggleFavorite);
    document.querySelector("#downloadPdfBtn").addEventListener("click", downloadPdf);
    window.setTimeout(() => output.classList.remove("switching-language"), 220);
    loadHistory();
    loadFavorites();
}

async function explainCode() {
    const codeInput = document.querySelector("#codeInput");
    const preference = document.querySelector("#languagePreference");
    const skillMode = document.querySelector("#skillMode");
    const output = document.querySelector("#outputContent");
    const explainBtn = document.querySelector("#explainBtn");

    output.className = "empty-state loading-state";
    output.innerHTML = `<span class="loader"></span><strong>Thinking through your code...</strong>`;
    explainBtn.disabled = true;
    explainBtn.classList.add("glow-pulse");

    try {
        const response = await fetch("/api/explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: codeInput.value,
                preference: preference.value,
                skill_mode: skillMode.value
            })
        });
        const data = await response.json();
        if (!response.ok) {
            output.className = "empty-state";
            output.textContent = data.error || "Something went wrong.";
            return;
        }
        renderExplanation(data);
    } finally {
        explainBtn.disabled = false;
        explainBtn.classList.remove("glow-pulse");
    }
}

async function loadHistory() {
    const response = await fetch("/api/history");
    const history = await response.json();
    const list = document.querySelector("#historyList");
    list.innerHTML = history.map((item) => `
        <button class="history-item" data-id="${item.id}" type="button">
            <strong>${item.language}</strong>
            <span>${new Date(item.created_at).toLocaleString()}</span>
        </button>
    `).join("") || `<p class="muted-text">No history yet.</p>`;
}

async function loadFavorites() {
    const response = await fetch("/api/favorites");
    const favorites = await response.json();
    const list = document.querySelector("#favoritesList");
    list.innerHTML = favorites.map((item) => `
        <button class="history-item" data-id="${item.history_id}" type="button">
            <strong>${item.title}</strong>
            <span>${new Date(item.created_at).toLocaleString()}</span>
        </button>
    `).join("") || `<p class="muted-text">No saved explanations yet.</p>`;
}

async function openHistory(historyId) {
    const response = await fetch(`/api/history/${historyId}`);
    const data = await response.json();
    if (response.ok) {
        document.querySelector("#codeInput").value = data.code;
        currentHistoryId = data.history_id;
        renderExplanation(data);
    }
}

async function toggleFavorite() {
    if (!currentHistoryId) {
        return;
    }
    await fetch(`/api/favorite/${currentHistoryId}`, { method: "POST" });
    loadFavorites();
}

function downloadPdf() {
    window.print();
}

function setupExamples() {
    const grid = document.querySelector("#exampleGrid");
    const codeInput = document.querySelector("#codeInput");
    grid.innerHTML = examples.map((example, index) => `
        <button class="example-card" type="button" data-index="${index}">
            <strong>${example.title}</strong>
            <span>Load example</span>
        </button>
    `).join("");
    grid.addEventListener("click", (event) => {
        const card = event.target.closest(".example-card");
        if (card) {
            codeInput.value = examples[Number(card.dataset.index)].code;
            codeInput.focus();
        }
    });
}

function setupThemeToggle() {
    const button = document.querySelector("#themeToggle");
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.body.dataset.theme = savedTheme;
    button.textContent = savedTheme === "dark" ? "Light" : "Dark";
    button.addEventListener("click", () => {
        const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
        document.body.dataset.theme = nextTheme;
        localStorage.setItem("theme", nextTheme);
        button.textContent = nextTheme === "dark" ? "Light" : "Dark";
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupThemeToggle();
    setupExamples();
    loadHistory();
    loadFavorites();

    document.querySelector("#explainBtn").addEventListener("click", explainCode);
    document.querySelector("#clearBtn").addEventListener("click", () => {
        document.querySelector("#codeInput").value = "";
        document.querySelector("#outputContent").className = "empty-state";
        document.querySelector("#outputContent").textContent = "Enter code and click Explain Code.";
        document.querySelector("#detectedLanguage").textContent = "Waiting";
        lastExplanationData = null;
        currentHistoryId = null;
    });
    document.querySelector("#languagePreference").addEventListener("change", () => {
        if (lastExplanationData) {
            renderExplanation(lastExplanationData);
        }
    });
    document.querySelector("#historyList").addEventListener("click", (event) => {
        const item = event.target.closest(".history-item");
        if (item) {
            openHistory(item.dataset.id);
        }
    });
    document.querySelector("#favoritesList").addEventListener("click", (event) => {
        const item = event.target.closest(".history-item");
        if (item) {
            openHistory(item.dataset.id);
        }
    });
});
