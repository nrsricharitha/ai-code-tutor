const codeInput = document.getElementById("codeInput");
const explainBtn = document.getElementById("explainBtn");
const clearBtn = document.getElementById("clearBtn");
const favoriteBtn = document.getElementById("favoriteBtn");
const downloadBtn = document.getElementById("downloadBtn");
const languageSelect = document.getElementById("languageSelect");
const codeLanguageSelect = document.getElementById("codeLanguageSelect");
const skillSelect = document.getElementById("skillSelect");
const statusPill = document.getElementById("statusPill");
const loader = document.getElementById("loader");
const overviewCard = document.getElementById("overviewCard");
const explanationOutput = document.getElementById("explanationOutput");
const conceptGrid = document.getElementById("conceptGrid");
const meterFill = document.getElementById("meterFill");
const complexityText = document.getElementById("complexityText");
const complexityReason = document.getElementById("complexityReason");
const errorList = document.getElementById("errorList");
const outputPrediction = document.getElementById("outputPrediction");
const roadmapList = document.getElementById("roadmapList");
const quizList = document.getElementById("quizList");
const quizScoreBadge = document.getElementById("quizScoreBadge");
const themeToggle = document.getElementById("themeToggle");
const programsStat = document.getElementById("programsStat");
const explanationsStat = document.getElementById("explanationsStat");
const levelStat = document.getElementById("levelStat");
const conceptsStat = document.getElementById("conceptsStat");

const allConcepts = [
    "Variables", "Input", "Output", "Loops", "Conditions",
    "Functions", "Arrays", "Classes", "Objects", "Recursion",
];

let currentHistoryId = null;
let quizScore = 0;
let quizTotal = 0;

function setStatus(text) {
    if (statusPill) statusPill.textContent = text;
}

function setLoading(isLoading) {
    loader?.classList.toggle("hidden", !isLoading);
    explainBtn?.toggleAttribute("disabled", isLoading);
    setStatus(isLoading ? "Analyzing…" : "Ready");
}

function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

function renderExplanation(data) {
    currentHistoryId = data.history_id || currentHistoryId;
    if (overviewCard) overviewCard.textContent = data.overview;
    if (explanationOutput) {
        explanationOutput.innerHTML = "";
        (data.items || []).forEach((item, index) => {
            const card = element("article", "line-card");
            card.style.animationDelay = `${index * 35}ms`;
            const header = element("div", "line-card-header");
            header.appendChild(element("h3", "", item.title));
            header.appendChild(element("span", "kind-pill", item.kind));
            card.appendChild(header);
            card.appendChild(element("div", "code-chip", item.code));
            card.appendChild(element("p", "", item.explanation));
            explanationOutput.appendChild(card);
        });
    }
    renderConcepts(data.concepts || {});
    renderComplexity(data.complexity || { level: "Beginner", score: 1, reason: "" });
    renderErrors(data.errors || []);
    renderRoadmap(data.roadmap || []);
    renderQuiz(data.quiz || []);
    if (outputPrediction) {
        outputPrediction.textContent = data.expected_output || "Output cannot be predicted safely.";
    }
    if (favoriteBtn) favoriteBtn.disabled = !currentHistoryId;
    if (downloadBtn && currentHistoryId) {
        downloadBtn.href = `/download/${currentHistoryId}`;
        downloadBtn.classList.remove("disabled");
        downloadBtn.setAttribute("aria-disabled", "false");
    }
    updateStats(data);
}

function renderConcepts(concepts) {
    if (!conceptGrid) return;
    conceptGrid.innerHTML = "";
    allConcepts.forEach((name) => {
        const active = !!concepts[name];
        const chip = element("div", `concept-chip ${active ? "active" : ""}`);
        chip.innerHTML = `<span class="check">${active ? "✓" : "—"}</span><span>${name}</span>`;
        conceptGrid.appendChild(chip);
    });
}

function renderComplexity(complexity) {
    const score = Number(complexity.score || 1);
    if (meterFill) meterFill.style.width = `${Math.min(100, score * 10)}%`;
    if (complexityText) {
        complexityText.textContent = `Complexity Level: ${complexity.level} (${score}/10)`;
    }
    if (complexityReason && complexity.reason) {
        complexityReason.textContent = complexity.reason;
    }
    if (levelStat) levelStat.textContent = complexity.level;
}

function renderErrors(errors) {
    if (!errorList) return;
    errorList.innerHTML = "";
    errors.forEach((error) => {
        const item = element("div", "mini-item");
        item.innerHTML = `<strong>Line ${error.line}</strong><span>${error.description}</span><small>${error.fix}</small>`;
        errorList.appendChild(item);
    });
}

function renderRoadmap(topics) {
    if (!roadmapList) return;
    roadmapList.innerHTML = "";
    topics.forEach((topic) => {
        const li = document.createElement("li");
        li.className = "roadmap-item";
        li.innerHTML = `<span class="roadmap-arrow">→</span><span>${topic}</span>`;
        roadmapList.appendChild(li);
    });
}

function renderQuiz(questions) {
    if (!quizList) return;
    quizList.innerHTML = "";
    quizScore = 0;
    quizTotal = questions.length;
    if (quizScoreBadge) quizScoreBadge.classList.add("hidden");

    questions.forEach((q, qi) => {
        if (typeof q === "string") {
            // fallback for plain-text questions
            const li = element("li", "quiz-item");
            li.innerHTML = `<div class="quiz-question">${qi + 1}. ${q}</div>`;
            quizList.appendChild(li);
            return;
        }

        const item = element("div", "quiz-item");
        const qEl = element("div", "quiz-question", `${qi + 1}. ${q.question}`);
        item.appendChild(qEl);

        const opts = element("div", "quiz-options");
        const labels = ["A", "B", "C", "D"];
        let answered = false;

        (q.options || []).forEach((opt, oi) => {
            const btn = document.createElement("button");
            btn.className = "quiz-option";
            btn.type = "button";
            btn.innerHTML = `<span class="quiz-option-label">${labels[oi]}</span>${opt}`;
            btn.addEventListener("click", () => {
                if (answered) return;
                answered = true;
                // Disable all options
                opts.querySelectorAll(".quiz-option").forEach(b => b.disabled = true);
                const isCorrect = oi === q.answer;
                btn.classList.add(isCorrect ? "correct" : "wrong");
                if (!isCorrect) {
                    opts.querySelectorAll(".quiz-option")[q.answer]?.classList.add("correct");
                }
                const fb = item.querySelector(".quiz-feedback");
                fb.className = `quiz-feedback show ${isCorrect ? "correct-msg" : "wrong-msg"}`;
                fb.textContent = isCorrect ? "✓ Correct!" : `✗ Incorrect. Correct answer: ${labels[q.answer]}. ${q.options[q.answer]}`;
                if (isCorrect) quizScore++;
                updateQuizScore();
            });
            opts.appendChild(btn);
        });

        item.appendChild(opts);
        const fb = element("div", "quiz-feedback");
        item.appendChild(fb);
        quizList.appendChild(item);
    });
}

function updateQuizScore() {
    const answered = document.querySelectorAll(".quiz-option.correct, .quiz-option.wrong").length > 0;
    const total = quizList.querySelectorAll(".quiz-item").length;
    const doneCount = quizList.querySelectorAll(".quiz-feedback.show").length;
    if (quizScoreBadge && doneCount > 0) {
        quizScoreBadge.classList.remove("hidden");
        quizScoreBadge.textContent = `Score: ${quizScore}/${doneCount}`;
    }
}

function updateStats(data) {
    const enabledConcepts = Object.values(data.concepts || {}).filter(Boolean).length;
    if (programsStat && data.history_id) {
        programsStat.textContent = String(Number(programsStat.textContent || "0") + 1);
    }
    if (explanationsStat && data.history_id) {
        explanationsStat.textContent = String(Number(explanationsStat.textContent || "0") + 1);
    }
    if (conceptsStat) {
        conceptsStat.textContent = String(Math.max(Number(conceptsStat.textContent || "0"), enabledConcepts));
    }
}

async function explainCode() {
    if (!codeInput || !languageSelect || !skillSelect || !codeLanguageSelect) return;
    setLoading(true);
    try {
        const response = await fetch("/explain-code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: codeInput.value,
                code_language: codeLanguageSelect.value,
                language: languageSelect.value,
                level: skillSelect.value,
            }),
        });
        if (!response.ok) throw new Error("Unable to analyze code.");
        const data = await response.json();
        renderExplanation(data);
        refreshHistoryItem(data);
        // Scroll to results
        document.getElementById("resultsSection")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
        if (overviewCard) overviewCard.textContent = error.message;
    } finally {
        setLoading(false);
    }
}

function refreshHistoryItem(data) {
    const historyList = document.getElementById("historyList");
    if (!historyList || !data.history_id || !codeInput.value.trim()) return;
    historyList.querySelector(".muted")?.remove();
    const button = element("button", "history-item");
    button.type = "button";
    button.dataset.historyId = data.history_id;
    const firstLine = codeInput.value.trim().split("\n")[0].slice(0, 60) || "Untitled analysis";
    const langLabel = codeLanguageSelect?.options[codeLanguageSelect.selectedIndex]?.text || data.code_language;
    button.innerHTML = `<span></span><small>${langLabel} • Just now</small>`;
    button.querySelector("span").textContent = firstLine;
    button.addEventListener("click", () => loadHistory(data.history_id));
    historyList.prepend(button);
}

async function loadHistory(historyId) {
    const response = await fetch(`/history/${historyId}`);
    if (!response.ok) return;
    const data = await response.json();
    currentHistoryId = historyId;
    if (codeInput) codeInput.value = data.code || "";
    renderExplanation(data);
}

async function saveFavorite() {
    if (!currentHistoryId) return;
    const response = await fetch(`/favorite/${currentHistoryId}`, { method: "POST" });
    if (response.ok) {
        favoriteBtn.textContent = "⭐ Saved!";
        setTimeout(() => { favoriteBtn.textContent = "⭐ Save Explanation"; }, 1800);
    }
}

function clearWorkspace() {
    currentHistoryId = null;
    if (codeInput) codeInput.value = "";
    if (overviewCard) overviewCard.textContent = "Paste code and press Explain Code.";
    if (explanationOutput) explanationOutput.innerHTML = "";
    renderConcepts({});
    renderComplexity({ level: "Not analyzed", score: 0, reason: "" });
    renderErrors([]);
    renderRoadmap([]);
    renderQuiz([]);
    if (outputPrediction) outputPrediction.textContent = "Not available yet.";
    if (favoriteBtn) favoriteBtn.disabled = true;
    if (downloadBtn) {
        downloadBtn.href = "#";
        downloadBtn.classList.add("disabled");
        downloadBtn.setAttribute("aria-disabled", "true");
    }
    if (complexityReason) complexityReason.textContent = "";
    if (quizScoreBadge) quizScoreBadge.classList.add("hidden");
}

function applyTheme(theme) {
    document.body.classList.toggle("light-mode", theme === "light");
    if (themeToggle) themeToggle.textContent = theme === "light" ? "☀" : "☾";
    localStorage.setItem("ai-code-tutor-theme", theme);
}

document.querySelectorAll(".history-item").forEach((button) => {
    button.addEventListener("click", () => loadHistory(button.dataset.historyId));
});

document.querySelectorAll("#favoritesList .history-item").forEach((button) => {
    button.addEventListener("click", () => loadHistory(button.dataset.historyId));
});

explainBtn?.addEventListener("click", explainCode);
clearBtn?.addEventListener("click", clearWorkspace);
favoriteBtn?.addEventListener("click", saveFavorite);
themeToggle?.addEventListener("click", () => {
    const next = document.body.classList.contains("light-mode") ? "dark" : "light";
    applyTheme(next);
});

applyTheme(localStorage.getItem("ai-code-tutor-theme") || "dark");
renderConcepts({});
