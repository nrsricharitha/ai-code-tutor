// ─── DOM refs ────────────────────────────────────────────────────────────────
const codeInput          = document.getElementById("codeInput");
const explainBtn         = document.getElementById("explainBtn");
const clearBtn           = document.getElementById("clearBtn");
const favoriteBtn        = document.getElementById("favoriteBtn");
const downloadBtn        = document.getElementById("downloadBtn");
const languageSelect     = document.getElementById("languageSelect");
const codeLanguageSelect = document.getElementById("codeLanguageSelect");
const skillSelect        = document.getElementById("skillSelect");
const statusPill         = document.getElementById("statusPill");
const loader             = document.getElementById("loader");
const overviewCard       = document.getElementById("overviewCard");
const explanationOutput  = document.getElementById("explanationOutput");
const conceptGrid        = document.getElementById("conceptGrid");
const meterFill          = document.getElementById("meterFill");
const complexityText     = document.getElementById("complexityText");
const complexityReason   = document.getElementById("complexityReason");
const errorList          = document.getElementById("errorList");
const outputPrediction   = document.getElementById("outputPrediction");
const roadmapList        = document.getElementById("roadmapList");
const quizList           = document.getElementById("quizList");
const quizScoreBadge     = document.getElementById("quizScoreBadge");
const themeToggle        = document.getElementById("themeToggle");
const programsStat       = document.getElementById("programsStat");
const explanationsStat   = document.getElementById("explanationsStat");
const levelStat          = document.getElementById("levelStat");
const conceptsStat       = document.getElementById("conceptsStat");
const feedbackBtn        = document.getElementById("feedbackBtn");
const feedbackModal      = document.getElementById("feedbackModal");
const feedbackClose      = document.getElementById("feedbackClose");
const feedbackSubmit     = document.getElementById("feedbackSubmit");
const feedbackMsg        = document.getElementById("feedbackMsg");
const starRow            = document.getElementById("starRow");
const starLabel          = document.getElementById("starLabel");
const feedbackCategory   = document.getElementById("feedbackCategory");
const feedbackComment    = document.getElementById("feedbackComment");
const voicePlayBtn       = document.getElementById("voicePlayBtn");
const voicePauseBtn      = document.getElementById("voicePauseBtn");
const voiceStopBtn       = document.getElementById("voiceStopBtn");
const voiceSpeedSelect   = document.getElementById("voiceSpeedSelect");
const startCamBtn        = document.getElementById("startCamBtn");
const attentionVideo     = document.getElementById("attentionVideo");
const attentionCanvas    = document.getElementById("attentionCanvas");
const attentionStatus    = document.getElementById("attentionStatus");
const attentionDot       = document.getElementById("attentionDot");
const attentionStatusText= document.getElementById("attentionStatusText");
const attentionBadge     = document.getElementById("attentionBadge");
const attentionLabel     = document.getElementById("attentionLabel");
const attentionIcon      = document.getElementById("attentionIcon");

const allConcepts = [
    "Variables","Input","Output","Loops","Conditions",
    "Functions","Arrays","Classes","Objects","Recursion",
];

// Language → Web Speech API BCP-47 locale
const WEB_SPEECH_LOCALES = {
    english: "en-IN", telugu: "te-IN", hindi: "hi-IN",
    marathi: "mr-IN", kannada: "kn-IN", tamil: "ta-IN",
};

const STAR_LABELS = ["","Poor","Fair","Good","Great","Excellent"];

let currentHistoryId = null;
let quizScore        = 0;
let quizTotal        = 0;
let selectedRating   = 0;

// ─── Voice / TTS ─────────────────────────────────────────────────────────────
let ttsAudio      = null;   // HTMLAudioElement for GCP audio
let ttsUtterance  = null;   // SpeechSynthesisUtterance for fallback
let ttsQueue      = [];     // array of text chunks
let ttsPlaying    = false;

function buildTTSText(data) {
    const parts = [];
    if (data.overview) parts.push(data.overview);
    (data.items || []).forEach(item => {
        parts.push(`${item.title}. ${item.explanation}`);
    });
    if (data.complexity?.level) {
        parts.push(`Complexity: ${data.complexity.level}. ${data.complexity.reason || ""}`);
    }
    return parts.join(" \n ");
}

function enableVoiceControls(enable) {
    if (voicePlayBtn)  voicePlayBtn.disabled  = !enable;
    if (voicePauseBtn) voicePauseBtn.disabled = !enable;
    if (voiceStopBtn)  voiceStopBtn.disabled  = !enable;
}

function stopTTS() {
    if (ttsAudio) { ttsAudio.pause(); ttsAudio = null; }
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    ttsPlaying = false;
    ttsQueue   = [];
    if (voicePlayBtn) voicePlayBtn.textContent = "▶ Read";
}

async function playTTS(text, language) {
    stopTTS();
    ttsPlaying = true;
    if (voicePlayBtn) voicePlayBtn.textContent = "⏳ Loading…";

    const speed = parseFloat(voiceSpeedSelect?.value || "1");

    try {
        const resp = await fetch("/tts", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({text, language}),
        });
        const data = await resp.json();

        if (data.fallback || data.error) {
            // Web Speech API fallback
            useBrowserTTS(text, language, speed);
            return;
        }

        // GCP audio (base64 MP3)
        const audioData = `data:audio/mp3;base64,${data.audioContent}`;
        ttsAudio = new Audio(audioData);
        ttsAudio.playbackRate = speed;
        ttsAudio.play();
        ttsAudio.onended = () => {
            ttsPlaying = false;
            if (voicePlayBtn) voicePlayBtn.textContent = "▶ Read";
        };
        if (voicePlayBtn) voicePlayBtn.textContent = "🔊 Playing";
    } catch {
        useBrowserTTS(text, language, speed);
    }
}

function useBrowserTTS(text, language, speed) {
    if (!window.speechSynthesis) {
        alert("Text-to-speech is not supported in this browser.");
        return;
    }
    const locale = WEB_SPEECH_LOCALES[language] || "en-IN";
    // Chunk text into ≤200-char sentences to avoid browser limits
    const sentences = text.match(/[^.!?\n]+[.!?\n]*/g) || [text];
    ttsQueue = sentences.slice();

    function speakNext() {
        if (!ttsQueue.length || !ttsPlaying) {
            ttsPlaying = false;
            if (voicePlayBtn) voicePlayBtn.textContent = "▶ Read";
            return;
        }
        const chunk = ttsQueue.shift();
        ttsUtterance = new SpeechSynthesisUtterance(chunk);
        ttsUtterance.lang = locale;
        ttsUtterance.rate = speed;
        ttsUtterance.onend = speakNext;
        window.speechSynthesis.speak(ttsUtterance);
    }

    if (voicePlayBtn) voicePlayBtn.textContent = "🔊 Playing";
    speakNext();
}

function pauseTTS() {
    if (ttsAudio) {
        ttsAudio.paused ? ttsAudio.play() : ttsAudio.pause();
        if (voicePlayBtn) voicePlayBtn.textContent = ttsAudio.paused ? "▶ Read" : "🔊 Playing";
    } else if (window.speechSynthesis) {
        if (window.speechSynthesis.paused) {
            window.speechSynthesis.resume();
            if (voicePlayBtn) voicePlayBtn.textContent = "🔊 Playing";
        } else {
            window.speechSynthesis.pause();
            if (voicePlayBtn) voicePlayBtn.textContent = "▶ Read";
        }
    }
}

// Store explanation data for voice button
let lastExplanationData = null;

voicePlayBtn?.addEventListener("click", () => {
    if (!lastExplanationData) return;
    const lang = languageSelect?.value || "english";
    const text = buildTTSText(lastExplanationData);
    playTTS(text, lang);
});
voicePauseBtn?.addEventListener("click", pauseTTS);
voiceStopBtn?.addEventListener("click", stopTTS);

// ─── Attention Monitor ───────────────────────────────────────────────────────
let camStream         = null;
let attentionInterval = null;
let prevBrightness    = null;
let distractedCount   = 0;

function setAttentionUI(status) {
    // status: "focused" | "distracted" | "away" | "off"
    const icons   = {focused:"✅", distracted:"⚠️", away:"😴", off:"👁"};
    const labels  = {focused:"Focused", distracted:"Distracted", away:"Away", off:"Cam Off"};
    const colors  = {focused:"var(--success)", distracted:"var(--amber)", away:"var(--danger)", off:"var(--muted)"};
    const dotCls  = {focused:"dot-green", distracted:"dot-amber", away:"dot-red", off:""};

    if (attentionIcon)  attentionIcon.textContent  = icons[status]  || "👁";
    if (attentionLabel) attentionLabel.textContent = labels[status] || "Off";
    if (attentionBadge) attentionBadge.style.color = colors[status] || "";

    if (attentionDot) {
        attentionDot.className = `attention-dot ${dotCls[status] || ""}`;
    }
    if (attentionStatusText) {
        const msgs = {focused:"You're focused 🎯", distracted:"Stay focused!", away:"Are you there? 👀", off:""};
        attentionStatusText.textContent = msgs[status] || "";
    }

    // Post to server (non-blocking)
    if (status !== "off" && currentHistoryId) {
        fetch("/attention", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({status, history_id: currentHistoryId}),
        }).catch(() => {});
    }
}

function computeBrightness(ctx, w, h) {
    const d = ctx.getImageData(0, 0, w, h).data;
    let sum = 0;
    for (let i = 0; i < d.length; i += 4) {
        sum += 0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2];
    }
    return sum / (d.length / 4);
}

function analyzeFrame() {
    if (!camStream || !attentionVideo || !attentionCanvas) return;
    const w = attentionVideo.videoWidth  || 160;
    const h = attentionVideo.videoHeight || 120;
    attentionCanvas.width  = w;
    attentionCanvas.height = h;
    const ctx = attentionCanvas.getContext("2d");
    ctx.drawImage(attentionVideo, 0, 0, w, h);
    const brightness = computeBrightness(ctx, w, h);

    // Very dark → away (face not visible / covered)
    if (brightness < 12) {
        distractedCount = 0;
        setAttentionUI("away");
        return;
    }

    // Motion delta: big change → head movement / distraction
    if (prevBrightness !== null) {
        const delta = Math.abs(brightness - prevBrightness);
        if (delta > 6) {
            distractedCount = Math.min(distractedCount + 1, 5);
        } else {
            distractedCount = Math.max(distractedCount - 1, 0);
        }
    }
    prevBrightness = brightness;

    setAttentionUI(distractedCount >= 3 ? "distracted" : "focused");
}

async function startCamera() {
    try {
        camStream = await navigator.mediaDevices.getUserMedia({video: {width:160, height:120}, audio:false});
        attentionVideo.srcObject = camStream;
        attentionVideo.play();

        if (startCamBtn) {
            startCamBtn.textContent = "Stop Camera";
            startCamBtn.className = "btn btn-secondary";
        }
        attentionStatus?.classList.remove("hidden");
        attentionInterval = setInterval(analyzeFrame, 1500);
        setAttentionUI("focused");
    } catch (err) {
        alert("Camera access denied or unavailable: " + err.message);
    }
}

function stopCamera() {
    if (camStream) {
        camStream.getTracks().forEach(t => t.stop());
        camStream = null;
    }
    clearInterval(attentionInterval);
    attentionInterval = null;
    attentionStatus?.classList.add("hidden");
    if (startCamBtn) {
        startCamBtn.textContent = "Start Camera";
        startCamBtn.className = "btn btn-secondary";
    }
    setAttentionUI("off");
}

startCamBtn?.addEventListener("click", () => {
    if (camStream) stopCamera(); else startCamera();
});

// ─── Feedback Modal ──────────────────────────────────────────────────────────
function openFeedback() {
    if (!feedbackModal) return;
    feedbackModal.classList.remove("hidden");
    selectedRating = 0;
    if (feedbackMsg)    feedbackMsg.textContent = "";
    if (feedbackComment) feedbackComment.value = "";
    updateStars(0);
}

function closeFeedback() {
    feedbackModal?.classList.add("hidden");
}

function updateStars(n) {
    starRow?.querySelectorAll(".star-btn").forEach((btn, i) => {
        btn.classList.toggle("active", i < n);
    });
    if (starLabel) starLabel.textContent = n ? STAR_LABELS[n] : "Tap a star to rate";
}

starRow?.querySelectorAll(".star-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        selectedRating = parseInt(btn.dataset.rating);
        updateStars(selectedRating);
    });
    btn.addEventListener("mouseenter", () => updateStars(parseInt(btn.dataset.rating)));
    btn.addEventListener("mouseleave", () => updateStars(selectedRating));
});

feedbackSubmit?.addEventListener("click", async () => {
    if (!selectedRating) { if (feedbackMsg) feedbackMsg.textContent = "Please select a rating."; return; }
    try {
        const resp = await fetch("/feedback", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({
                rating: selectedRating,
                category: feedbackCategory?.value || "general",
                comment: feedbackComment?.value || "",
                history_id: currentHistoryId,
            }),
        });
        if (resp.ok) {
            if (feedbackMsg) { feedbackMsg.textContent = "✅ Thanks for your feedback!"; feedbackMsg.style.color = "var(--success)"; }
            setTimeout(closeFeedback, 1600);
        } else {
            if (feedbackMsg) feedbackMsg.textContent = "Failed to save. Try again.";
        }
    } catch {
        if (feedbackMsg) feedbackMsg.textContent = "Network error.";
    }
});

feedbackBtn?.addEventListener("click", openFeedback);
feedbackClose?.addEventListener("click", closeFeedback);
feedbackModal?.addEventListener("click", (e) => { if (e.target === feedbackModal) closeFeedback(); });

// ─── Core logic (unchanged + voice hook) ────────────────────────────────────
function setStatus(text) { if (statusPill) statusPill.textContent = text; }

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
    lastExplanationData = data;
    enableVoiceControls(true);
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
    if (outputPrediction) outputPrediction.textContent = data.expected_output || "Output cannot be predicted safely.";
    if (favoriteBtn) favoriteBtn.disabled = !currentHistoryId;
    if (downloadBtn && currentHistoryId) {
        downloadBtn.href = `/download/${currentHistoryId}`;
        downloadBtn.classList.remove("disabled");
        downloadBtn.setAttribute("aria-disabled", "false");
    }
    updateStats(data);

    // Auto-read if language is non-English
    const lang = languageSelect?.value || "english";
    if (lang !== "english" && data.overview) {
        setTimeout(() => playTTS(buildTTSText(data), lang), 600);
    }
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
    if (complexityText) complexityText.textContent = `Complexity Level: ${complexity.level} (${score}/10)`;
    if (complexityReason && complexity.reason) complexityReason.textContent = complexity.reason;
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
            const li = element("li", "quiz-item");
            li.innerHTML = `<div class="quiz-question">${qi + 1}. ${q}</div>`;
            quizList.appendChild(li);
            return;
        }
        const item = element("div", "quiz-item");
        const qEl = element("div", "quiz-question", `${qi + 1}. ${q.question}`);
        item.appendChild(qEl);
        const opts = element("div", "quiz-options");
        const labels = ["A","B","C","D"];
        let answered = false;
        (q.options || []).forEach((opt, oi) => {
            const btn = document.createElement("button");
            btn.className = "quiz-option";
            btn.type = "button";
            btn.innerHTML = `<span class="quiz-option-label">${labels[oi]}</span>${opt}`;
            btn.addEventListener("click", () => {
                if (answered) return;
                answered = true;
                opts.querySelectorAll(".quiz-option").forEach(b => b.disabled = true);
                const isCorrect = oi === q.answer;
                btn.classList.add(isCorrect ? "correct" : "wrong");
                if (!isCorrect) opts.querySelectorAll(".quiz-option")[q.answer]?.classList.add("correct");
                const fb = item.querySelector(".quiz-feedback");
                fb.className = `quiz-feedback show ${isCorrect ? "correct-msg" : "wrong-msg"}`;
                fb.textContent = isCorrect ? "✓ Correct!" : `✗ Incorrect. Correct answer: ${labels[q.answer]}. ${q.options[q.answer]}`;
                if (isCorrect) quizScore++;
                updateQuizScore();
            });
            opts.appendChild(btn);
        });
        item.appendChild(opts);
        item.appendChild(element("div", "quiz-feedback"));
        quizList.appendChild(item);
    });
}

function updateQuizScore() {
    const doneCount = quizList.querySelectorAll(".quiz-feedback.show").length;
    if (quizScoreBadge && doneCount > 0) {
        quizScoreBadge.classList.remove("hidden");
        quizScoreBadge.textContent = `Score: ${quizScore}/${doneCount}`;
    }
}

function updateStats(data) {
    const enabledConcepts = Object.values(data.concepts || {}).filter(Boolean).length;
    if (programsStat && data.history_id) programsStat.textContent = String(Number(programsStat.textContent||"0")+1);
    if (explanationsStat && data.history_id) explanationsStat.textContent = String(Number(explanationsStat.textContent||"0")+1);
    if (conceptsStat) conceptsStat.textContent = String(Math.max(Number(conceptsStat.textContent||"0"), enabledConcepts));
}

async function explainCode() {
    if (!codeInput || !languageSelect || !skillSelect || !codeLanguageSelect) return;
    setLoading(true);
    stopTTS();
    try {
        const response = await fetch("/explain-code", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
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
        document.getElementById("resultsSection")?.scrollIntoView({behavior:"smooth",block:"start"});
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
    const firstLine = codeInput.value.trim().split("\n")[0].slice(0,60) || "Untitled analysis";
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
    const response = await fetch(`/favorite/${currentHistoryId}`, {method:"POST"});
    if (response.ok) {
        favoriteBtn.textContent = "⭐ Saved!";
        setTimeout(() => { favoriteBtn.textContent = "⭐ Save Explanation"; }, 1800);
    }
}

function clearWorkspace() {
    currentHistoryId = null;
    lastExplanationData = null;
    enableVoiceControls(false);
    stopTTS();
    if (codeInput) codeInput.value = "";
    if (overviewCard) overviewCard.textContent = "Paste code and press Explain Code.";
    if (explanationOutput) explanationOutput.innerHTML = "";
    renderConcepts({});
    renderComplexity({level:"Not analyzed",score:0,reason:""});
    renderErrors([]);
    renderRoadmap([]);
    renderQuiz([]);
    if (outputPrediction) outputPrediction.textContent = "Not available yet.";
    if (favoriteBtn) favoriteBtn.disabled = true;
    if (downloadBtn) { downloadBtn.href="#"; downloadBtn.classList.add("disabled"); downloadBtn.setAttribute("aria-disabled","true"); }
    if (complexityReason) complexityReason.textContent = "";
    if (quizScoreBadge) quizScoreBadge.classList.add("hidden");
}

function applyTheme(theme) {
    document.body.classList.toggle("light-mode", theme === "light");
    if (themeToggle) themeToggle.textContent = theme === "light" ? "☀" : "☾";
    localStorage.setItem("ai-code-tutor-theme", theme);
}

// ─── Event wiring ─────────────────────────────────────────────────────────────
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
    applyTheme(document.body.classList.contains("light-mode") ? "dark" : "light");
});

// ─── Init ────────────────────────────────────────────────────────────────────
applyTheme(localStorage.getItem("ai-code-tutor-theme") || "dark");
renderConcepts({});
enableVoiceControls(false);
