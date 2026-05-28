// Built-in examples help beginners test the tutor immediately.
const examples = [
    {
        title: "Addition Program",
        code: `a = int(input("Enter first number: "))
b = int(input("Enter second number: "))
sum = a + b
print("Sum is", sum)`
    },
    {
        title: "For Loop",
        code: `for i in range(5):
    print(i)`
    },
    {
        title: "If Else",
        code: `age = 18
if age >= 18:
    print("You can vote")
else:
    print("You cannot vote")`
    },
    {
        title: "Function Example",
        code: `function greet(name) {
    console.log("Hello " + name);
}
greet("Student");`
    },
    {
        title: "Array Example",
        code: `let marks = [80, 90, 75, 88];
for (let i = 0; i < marks.length; i++) {
    console.log(marks[i]);
}`
    }
];

let lastSpeechChunks = [];
let lastExplanationData = null;
let recognition = null;

const speechLanguageCodes = {
    English: "en-US",
    Telugu: "te-IN",
    Hindi: "hi-IN",
    Marathi: "mr-IN",
    Kannada: "kn-IN",
    Tamil: "ta-IN"
};

function languagesForPreference(preference, data) {
    const allLanguages = data?.supported_languages || ["English", "Telugu", "Hindi", "Marathi", "Kannada", "Tamil"];
    if (preference === "Multiple Languages" || preference === "Both") {
        return allLanguages;
    }
    return allLanguages.includes(preference) ? [preference] : ["English"];
}

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

function normalizeSpokenCode(transcript) {
    return transcript
        .replace(/\bnew line\b/gi, "\n")
        .replace(/\btab\b/gi, "    ")
        .replace(/\bopen parenthesis\b/gi, "(")
        .replace(/\bclose parenthesis\b/gi, ")")
        .replace(/\bopen bracket\b/gi, "[")
        .replace(/\bclose bracket\b/gi, "]")
        .replace(/\bopen brace\b/gi, "{")
        .replace(/\bclose brace\b/gi, "}")
        .replace(/\bcolon\b/gi, ":")
        .replace(/\bsemicolon\b/gi, ";")
        .replace(/\bcomma\b/gi, ",")
        .replace(/\bdot\b/gi, ".")
        .replace(/\bequals\b/gi, "=")
        .replace(/\bplus\b/gi, "+")
        .replace(/\bminus\b/gi, "-")
        .replace(/\btimes\b/gi, "*")
        .replace(/\bdivide\b/gi, "/")
        .replace(/\bdouble quote\b/gi, "\"")
        .replace(/\bsingle quote\b/gi, "'")
        .trim();
}

function renderExplanation(data) {
    const output = document.querySelector("#outputContent");
    const badge = document.querySelector("#detectedLanguage");
    const preference = document.querySelector("#languagePreference")?.value || data.preference;
    const languages = languagesForPreference(preference, data);
    const speechChunks = [];

    badge.textContent = data.language;

    const lines = data.lines.map((line) => {
        const explanations = languages.map((language) => {
            const text = line.explanations[language] || "";
            speechChunks.push({ language, text: `Line ${line.number}. ${text}` });
            return `<p><strong class="speech-label">${language}:</strong> <span class="speakable-text">${text}</span></p>`;
        }).join("");

        return `
            <article class="line-card">
                <div class="line-code">
                    <span>Line ${line.number}</span>
                    <code>${escapeHtml(line.code || "blank line")}</code>
                </div>
                <div class="line-explanations">${explanations}</div>
            </article>
        `;
    }).join("");

    const errors = data.errors.length
        ? data.errors.map((error) => `
            <li>
                <strong>${error.title}${error.line ? ` on line ${error.line}` : ""}:</strong>
                ${error.message} ${error.fix}
            </li>
        `).join("")
        : "<li>No common beginner mistakes detected.</li>";

    const summaries = languages.map((language) => {
        const text = data.summaries[language] || "";
        speechChunks.push({ language, text });
        return `<p><strong class="speech-label">${language}:</strong> <span class="speakable-text">${text}</span></p>`;
    }).join("");

    const analogies = languages.map((language) => {
        const text = data.analogies[language] || "";
        speechChunks.push({ language, text });
        return `<p><strong class="speech-label">${language}:</strong> <span class="speakable-text">${text}</span></p>`;
    }).join("");

    lastSpeechChunks = speechChunks.filter((chunk) => chunk.text.trim());
    lastExplanationData = data;

    output.className = "explanation-content";
    output.classList.add("switching-language");
    output.innerHTML = `
        <div class="summary-card">
            <p class="mode-note">${data.mode_note}</p>
            <h3>Summary</h3>
            ${summaries}
            <h3>Real-life Analogy</h3>
            ${analogies}
        </div>
        <div class="summary-card">
            <h3>Error Check</h3>
            <ul>${errors}</ul>
        </div>
        ${lines}
    `;
    window.setTimeout(() => output.classList.remove("switching-language"), 220);
}

async function explainCode() {
    const codeInput = document.querySelector("#codeInput");
    const preference = document.querySelector("#languagePreference");
    const skillMode = document.querySelector("#skillMode");
    const output = document.querySelector("#outputContent");
    const explainBtn = document.querySelector("#explainBtn");

    output.className = "empty-state loading-state";
    output.innerHTML = `<span class="loader"></span><strong>Thinking through your code...</strong>`;
    explainBtn?.classList.add("glow-pulse");
    if (explainBtn) {
        explainBtn.disabled = true;
    }

    try {
        const response = await fetch("/api/explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: codeInput.value,
                preference: preference.value,
                skill_mode: skillMode ? skillMode.value : "Beginner"
            })
        });

        const data = await response.json();
        if (!response.ok) {
            output.className = "empty-state";
            output.textContent = data.error || "Something went wrong.";
            return false;
        }

        renderExplanation(data);
        return true;
    } finally {
        explainBtn?.classList.remove("glow-pulse");
        if (explainBtn) {
            explainBtn.disabled = false;
        }
    }
}

function setupVoiceInput() {
    const speakBtn = document.querySelector("#speakCodeBtn");
    const codeInput = document.querySelector("#codeInput");
    const voiceStatus = document.querySelector("#voiceStatus");
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!speakBtn || !codeInput || !voiceStatus) {
        return;
    }

    if (!SpeechRecognition) {
        speakBtn.disabled = true;
        voiceStatus.querySelector("strong").textContent = "Speech recognition is not supported in this browser.";
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = false;

    speakBtn.addEventListener("click", () => {
        voiceStatus.classList.add("listening");
        speakBtn.classList.add("recording");
        voiceStatus.querySelector("strong").textContent = "Listening... speak your code now";
        try {
            recognition.start();
        } catch {
            voiceStatus.querySelector("strong").textContent = "Microphone is already listening.";
        }
    });

    recognition.onresult = async (event) => {
        const spokenCode = normalizeSpokenCode(event.results[0][0].transcript);
        codeInput.value = codeInput.value ? `${codeInput.value}\n${spokenCode}` : spokenCode;
        voiceStatus.querySelector("strong").textContent = "Voice captured. Explaining now...";
        const explained = await explainCode();
        if (explained) {
            readExplanationAloud();
        }
    };

    recognition.onerror = () => {
        voiceStatus.querySelector("strong").textContent = "Could not capture voice. Please try again.";
    };

    recognition.onend = () => {
        voiceStatus.classList.remove("listening");
        speakBtn.classList.remove("recording");
    };
}

function readExplanationAloud() {
    const voiceStatus = document.querySelector("#voiceStatus");
    if (!voiceStatus) {
        return;
    }

    if (!window.speechSynthesis) {
        voiceStatus.querySelector("strong").textContent = "Speech reading is not supported in this browser.";
        return;
    }

    if (!lastSpeechChunks.length) {
        voiceStatus.querySelector("strong").textContent = "Generate an explanation before reading it aloud.";
        return;
    }

    window.speechSynthesis.cancel();
    lastSpeechChunks.forEach((chunk) => {
        const speech = new SpeechSynthesisUtterance(chunk.text);
        speech.lang = speechLanguageCodes[chunk.language] || "en-US";
        speech.rate = 0.9;
        speech.pitch = 1;
        window.speechSynthesis.speak(speech);
    });
    voiceStatus.querySelector("strong").textContent = "Reading explanation aloud";
}

function setupSpeechOutput() {
    const readBtn = document.querySelector("#readExplanationBtn");
    if (readBtn) {
        readBtn.addEventListener("click", readExplanationAloud);
    }
}

function setupLanguageSwitching() {
    const preference = document.querySelector("#languagePreference");
    const voiceStatus = document.querySelector("#voiceStatus");

    if (!preference) {
        return;
    }

    preference.addEventListener("change", async () => {
        window.speechSynthesis?.cancel();
        if (lastExplanationData) {
            renderExplanation(lastExplanationData);
            if (voiceStatus) {
                voiceStatus.querySelector("strong").textContent = `Explanation switched to ${preference.value}`;
            }
            return;
        }

        const codeInput = document.querySelector("#codeInput");
        if (codeInput && codeInput.value.trim()) {
            await explainCode();
        }
    });
}

function setupExamples() {
    const grid = document.querySelector("#exampleGrid");
    const codeInput = document.querySelector("#codeInput");
    const loadExampleBtn = document.querySelector("#loadExampleBtn");

    if (!grid || !codeInput) {
        return;
    }

    grid.innerHTML = examples.map((example, index) => `
        <button class="example-card" type="button" data-index="${index}">
            <strong>${example.title}</strong>
            <span>Load into editor</span>
        </button>
    `).join("");

    grid.addEventListener("click", (event) => {
        const card = event.target.closest(".example-card");
        if (!card) {
            return;
        }
        codeInput.value = examples[Number(card.dataset.index)].code;
        codeInput.focus();
    });

    loadExampleBtn?.addEventListener("click", () => {
        codeInput.value = examples[0].code;
        codeInput.focus();
    });
}

function setupThemeToggle() {
    const button = document.querySelector("#themeToggle");
    const savedTheme = localStorage.getItem("theme") || "dark";

    document.body.dataset.theme = savedTheme;
    if (button) {
        button.textContent = savedTheme === "dark" ? "Light" : "Dark";
        button.addEventListener("click", () => {
            const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
            document.body.dataset.theme = nextTheme;
            localStorage.setItem("theme", nextTheme);
            button.textContent = nextTheme === "dark" ? "Light" : "Dark";
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    setupThemeToggle();
    setupExamples();
    setupVoiceInput();
    setupSpeechOutput();
    setupLanguageSwitching();

    const explainBtn = document.querySelector("#explainBtn");
    const clearBtn = document.querySelector("#clearBtn");
    const codeInput = document.querySelector("#codeInput");
    const output = document.querySelector("#outputContent");
    const badge = document.querySelector("#detectedLanguage");

    explainBtn?.addEventListener("click", explainCode);

    clearBtn?.addEventListener("click", () => {
        codeInput.value = "";
        output.className = "empty-state";
        output.textContent = "Enter code and click Explain Code.";
        badge.textContent = "Waiting";
        lastSpeechChunks = [];
        lastExplanationData = null;
        window.speechSynthesis?.cancel();
    });
});
