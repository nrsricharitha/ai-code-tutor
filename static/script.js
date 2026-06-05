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
const errorList = document.getElementById("errorList");
const outputPrediction = document.getElementById("outputPrediction");
const roadmapList = document.getElementById("roadmapList");
const quizList = document.getElementById("quizList");
const themeToggle = document.getElementById("themeToggle");
const programsStat = document.getElementById("programsStat");
const explanationsStat = document.getElementById("explanationsStat");
const levelStat = document.getElementById("levelStat");
const conceptsStat = document.getElementById("conceptsStat");

const allConcepts = [
    "Variables",
    "Loops",
    "Conditions",
    "Functions",
    "Arrays",
    "Classes",
    "Objects",
    "Recursion",
];

let currentHistoryId = null;

function setStatus(text) {
    if (statusPill) {
        statusPill.textContent = text;
    }
}

function setLoading(isLoading) {
    loader?.classList.toggle("hidden", !isLoading);
    explainBtn?.toggleAttribute("disabled", isLoading);
    setStatus(isLoading ? "Analyzing" : "Ready");
}

function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) {
        node.className = className;
    }
    if (text !== undefined) {
        node.textContent = text;
    }
    return node;
}

function renderExplanation(data) {
    currentHistoryId = data.history_id || currentHistoryId;
    if (overviewCard) {
        overviewCard.textContent = data.overview;
    }
    if (explanationOutput) {
        explanationOutput.innerHTML = "";
        data.items.forEach((item, index) => {
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
    renderComplexity(data.complexity || { level: "Beginner", score: 1 });
    renderErrors(data.errors || []);
    renderRoadmap(data.roadmap || []);
    renderQuiz(data.quiz || []);
    if (outputPrediction) {
        outputPrediction.textContent = data.expected_output || "Output cannot be predicted safely.";
    }
    if (favoriteBtn) {
        favoriteBtn.disabled = !currentHistoryId;
    }
    if (downloadBtn && currentHistoryId) {
        downloadBtn.href = `/download/${currentHistoryId}`;
        downloadBtn.classList.remove("disabled");
        downloadBtn.setAttribute("aria-disabled", "false");
    }
    updateStats(data);
}

function renderConcepts(concepts) {
    if (!conceptGrid) {
        return;
    }
    conceptGrid.innerHTML = "";
    allConcepts.forEach((name) => {
        const chip = element("div", `concept-chip ${concepts[name] ? "active" : ""}`);
        chip.innerHTML = `<span class="check">${concepts[name] ? "&#10003;" : "—"}</span><span>${name}</span>`;
        conceptGrid.appendChild(chip);
    });
}

function renderComplexity(complexity) {
    const score = Number(complexity.score || 1);
    if (meterFill) {
        meterFill.style.width = `${Math.min(100, score * 10)}%`;
    }
    if (complexityText) {
        complexityText.textContent = `Complexity Level: ${complexity.level} (${score}/10)`;
    }
    if (levelStat) {
        levelStat.textContent = complexity.level;
    }
}

function renderErrors(errors) {
    if (!errorList) {
        return;
    }
    errorList.innerHTML = "";
    errors.forEach((error) => {
        const item = element("div", "mini-item");
        item.innerHTML = `<strong>Line ${error.line}</strong><span>${error.description}</span><small>${error.fix}</small>`;
        errorList.appendChild(item);
    });
}

function renderRoadmap(topics) {
    if (!roadmapList) {
        return;
    }
    roadmapList.innerHTML = "";
    topics.forEach((topic) => {
        roadmapList.appendChild(element("li", "mini-item", topic));
    });
}

function renderQuiz(questions) {
    if (!quizList) {
        return;
    }
    quizList.innerHTML = "";
    questions.forEach((question) => {
        quizList.appendChild(element("li", "", question));
    });
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
    if (!codeInput || !languageSelect || !skillSelect || !codeLanguageSelect) {
        return;
    }
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
        if (!response.ok) {
            throw new Error("Unable to analyze code.");
        }
        const data = await response.json();
        renderExplanation(data);
        refreshHistoryItem(data);
    } catch (error) {
        if (overviewCard) {
            overviewCard.textContent = error.message;
        }
    } finally {
        setLoading(false);
    }
}

function refreshHistoryItem(data) {
    const historyList = document.getElementById("historyList");
    if (!historyList || !data.history_id || !codeInput.value.trim()) {
        return;
    }
    const empty = historyList.querySelector(".muted");
    empty?.remove();
    const button = element("button", "history-item");
    button.type = "button";
    button.dataset.historyId = data.history_id;
    const firstLine = codeInput.value.trim().split("\n")[0].slice(0, 70) || "Untitled analysis";
    button.innerHTML = `<span></span><small>${data.code_language} • Just now</small>`;
    button.querySelector("span").textContent = firstLine;
    button.addEventListener("click", () => loadHistory(data.history_id));
    historyList.prepend(button);
}

async function loadHistory(historyId) {
    const response = await fetch(`/history/${historyId}`);
    if (!response.ok) {
        return;
    }
    const data = await response.json();
    currentHistoryId = historyId;
    if (codeInput) {
        codeInput.value = data.code || "";
    }
    renderExplanation(data);
}

async function saveFavorite() {
    if (!currentHistoryId) {
        return;
    }
    const response = await fetch(`/favorite/${currentHistoryId}`, { method: "POST" });
    if (response.ok) {
        favoriteBtn.textContent = "Saved";
        setTimeout(() => {
            favoriteBtn.textContent = "Save Favorite";
        }, 1400);
    }
}

function clearWorkspace() {
    currentHistoryId = null;
    if (codeInput) {
        codeInput.value = "";
    }
    if (overviewCard) {
        overviewCard.textContent = "Paste code and press Explain Code.";
    }
    explanationOutput && (explanationOutput.innerHTML = "");
    renderConcepts({});
    renderComplexity({ level: "Not analyzed", score: 0 });
    renderErrors([]);
    renderRoadmap([]);
    renderQuiz([]);
    if (outputPrediction) {
        outputPrediction.textContent = "Not available yet.";
    }
    favoriteBtn && (favoriteBtn.disabled = true);
    if (downloadBtn) {
        downloadBtn.href = "#";
        downloadBtn.classList.add("disabled");
        downloadBtn.setAttribute("aria-disabled", "true");
    }
}

function applyTheme(theme) {
    document.body.classList.toggle("light-mode", theme === "light");
    if (themeToggle) {
        themeToggle.textContent = theme === "light" ? "☀" : "☾";
    }
    localStorage.setItem("ai-code-tutor-theme", theme);
}

document.querySelectorAll(".history-item").forEach((button) => {
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
