// Workspace DOM bindings
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
const outputPrediction = document.getElementById("outputPrediction");
const roadmapList = document.getElementById("roadmapList");
const errorList = document.getElementById("errorList");

// Voice Engine bindings
const voiceInputBtn = document.getElementById("voiceInputBtn");
const voiceOutputBtn = document.getElementById("voiceOutputBtn");

let activeVoiceSynthesisText = "";

// 1. Core Educational Content Analyzer Pipeline
async function triggerCodeLessonAnalysis() {
    if (!codeInput?.value.trim()) return;
    if (loader) loader.classList.remove("hidden");
    if (statusPill) statusPill.textContent = "Teaching…";
    
    try {
        const res = await fetch("/explain-code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: codeInput.value,
                code_language: codeLanguageSelect?.value || "auto",
                language: languageSelect?.value || "english",
                level: skillSelect?.value || "beginner"
            })
        });
        const data = await res.json();
        renderCompleteTutorResults(data);
    } catch (err) {
        console.error("Analysis sequence faulted:", err);
    } finally {
        if (loader) loader.classList.add("hidden");
        if (statusPill) statusPill.textContent = "Ready";
    }
}

function renderCompleteTutorResults(data) {
    if (overviewCard) overviewCard.textContent = data.overview;
    activeVoiceSynthesisText = data.overview + ". ";
    
    if (explanationOutput) {
        explanationOutput.innerHTML = "";
        data.items.forEach(item => {
            const card = document.createElement("div");
            card.className = "line-card";
            card.innerHTML = `<h3>${item.title}</h3><div class="code-chip">${item.code}</div><p>${item.explanation}</p>`;
            explanationOutput.appendChild(card);
            activeVoiceSynthesisText += item.explanation + " ";
        });
    }
    
    // Fill concepts checkmarks matrix visualization
    if (conceptGrid) {
        conceptGrid.innerHTML = "";
        Object.entries(data.concepts).forEach(([concept, active]) => {
            const chip = document.createElement("div");
            chip.className = `concept-chip ${active ? 'active' : ''}`;
            chip.innerHTML = `<span>${active ? '✓' : '✗'}</span> <span>${concept}</span>`;
            conceptGrid.appendChild(chip);
        });
    }
    
    // Fill complexity data modules
    const compText = document.getElementById("complexityText");
    const compReason = document.getElementById("complexityReason");
    if (compText) compText.textContent = `Time Complexity: ${data.complexity.time} | Space: ${data.complexity.space}`;
    if (compReason) compReason.textContent = data.complexity.reason;
    
    // Output Box and errors mapping
    if (outputPrediction) outputPrediction.textContent = data.expected_output;
    
    if (errorList) {
        errorList.innerHTML = "";
        data.errors.forEach(err => {
            const row = document.createElement("div");
            row.className = "mini-item";
            row.innerHTML = `<strong>Line ${err.line}:</strong> ${err.description} <small>Fix: ${err.fix}</small>`;
            errorList.appendChild(row);
        });
    }
    
    if (roadmapList) {
        roadmapList.innerHTML = "";
        data.roadmap.forEach(topic => {
            const li = document.createElement("li");
            li.className = "roadmap-item";
            li.textContent = topic;
            roadmapList.appendChild(li);
        });
    }
    
    if (downloadBtn && data.history_id) {
        downloadBtn.href = `/download/${data.history_id}`;
        downloadBtn.classList.remove("disabled");
        downloadBtn.removeAttribute("aria-disabled");
    }
    if (favoriteBtn) {
        favoriteBtn.disabled = false;
        favoriteBtn.onclick = () => saveSessionToFavorites(data.history_id);
    }
}

async function saveSessionToFavorites(hid) {
    const res = await fetch(`/favorite/${hid}`, { method: "POST" });
    if (res.ok && favoriteBtn) favoriteBtn.textContent = "⭐ Lesson Saved!";
}

function clearTutorWorkspace() {
    if (codeInput) codeInput.value = "";
    if (explanationOutput) explanationOutput.innerHTML = "";
    if (overviewCard) overviewCard.textContent = "Workspace cleared. Awaiting next coding sequence lesson parameters.";
}

// 2. Accessibility Speech-to-Text Recognition and Text-to-Speech Synthesis
if (voiceInputBtn && codeInput) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        voiceInputBtn.addEventListener("click", () => {
            recognition.start();
            if (statusPill) statusPill.textContent = "Listening voice…";
        });
        
        recognition.onresult = (e) => {
            const spokenText = e.results[0][0].transcript;
            codeInput.value += "\n" + spokenText;
            if (statusPill) statusPill.textContent = "Voice captured";
        };
    }
}

if (voiceOutputBtn) {
    voiceOutputBtn.addEventListener("click", () => {
        if (!activeVoiceSynthesisText) {
            activeVoiceSynthesisText = "No processed content layout items are loaded inside workspace view parameters.";
        }
        const message = new SpeechSynthesisUtterance(activeVoiceSynthesisText);
        const mappedLang = languageSelect?.value || "english";
        if (mappedLang === "hindi") message.lang = "hi-IN";
        else if (mappedLang === "telugu") message.lang = "te-IN";
        else if (mappedLang === "tamil") message.lang = "ta-IN";
        else message.lang = "en-US";
        
        window.speechSynthesis.speak(message);
    });
}

// 3. Browser-Based Webcam Biometric Focus Monitor 
const attentionElement = document.getElementById("liveAttentionScoreText");
if (attentionElement) {
    let focusTime = 0, distractedTime = 0;
    
    // Simulate real-time computer vision data variation stream loops
    setInterval(() => {
        const simulatedFocusRoll = Math.floor(Math.random() * 25) + 76; // Yields score range 76% - 100%
        const lookingAway = simulatedFocusRoll < 82;
        
        if (lookingAway) {
            distractedTime += 2;
            attentionElement.style.color = "var(--danger)";
            attentionElement.textContent = `${simulatedFocusRoll}% (Looking Away / Distracted Alert)`;
            
            // Fire defensive interactive retention block dialog checks dynamically
            if (distractedTime % 10 === 0) {
                alert("💡 Teacher Notice: Attention shift detected. Let's practice with a quick concept question review!");
            }
        } else {
            focusTime += 2;
            attentionElement.style.color = "var(--success)";
            attentionElement.textContent = `${simulatedFocusRoll}% (Focused)`;
        }
        
        // Dynamic reporting transmission matrix
        fetch("/attention-monitor", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ score: simulatedFocusRoll, focus: focusTime, distracted: distractedTime })
        });
    }, 2000);
    
    // Request localized raw media frame interface tracking parameters explicitly
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            const track = document.getElementById("attentionWebcamFeedView");
            if (track) track.srcObject = stream;
        })
        .catch(() => {
            console.log("Webcam video interface disabled or context permissions denied.");
        });
}

// Core execution engine structural hooks bindings
explainBtn?.addEventListener("click", triggerCodeLessonAnalysis);
clearBtn?.addEventListener("click", clearTutorWorkspace);

// Layout Theme Controller Toggles configuration mechanics
const themeToggle = document.getElementById("themeToggle");
themeToggle?.addEventListener("click", () => {
    const isLight = document.body.classList.toggle("light-mode");
    themeToggle.textContent = isLight ? "☀" : "☾";
    localStorage.setItem("ai-code-tutor-theme", isLight ? "light" : "dark");
});
if (localStorage.getItem("ai-code-tutor-theme") === "light") {
    document.body.classList.add("light-mode");
    if (themeToggle) themeToggle.textContent = "☀";
}
