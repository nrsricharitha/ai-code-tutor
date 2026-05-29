# FULL UPDATED script.js

```javascript
async function explainCode() {

    const code = document.getElementById("codeInput").value;
    const language =
        document.getElementById("languagePreference").value;

    const output =
        document.getElementById("outputContent");

    output.innerHTML =
        "<p>AI is analyzing your code...</p>";

    const response = await fetch("/api/explain", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            code: code,
            language: language
        })
    });

    const data = await response.json();

    let html = "";

    data.lines.forEach((line) => {

        html += `
        <div class="line-card">

            <div class="line-number">
                Line ${line.number}
            </div>

            <pre>${line.code}</pre>

            <div class="explanation">
                ${line.explanation}
            </div>

        </div>
        `;
    });

    output.innerHTML = html;
}

document
    .getElementById("explainBtn")
    .addEventListener("click", explainCode);

function readExplanation() {

    const text =
        document.getElementById("outputContent")
        .innerText;

    const speech =
        new SpeechSynthesisUtterance(text);

    speech.rate = 0.8;

    speech.pitch = 1;

    speech.volume = 1;

    window.speechSynthesis.speak(speech);
}

document
    .getElementById("readBtn")
    .addEventListener("click", readExplanation);

function startVoiceInput() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Voice input not supported");
        return;
    }

    const recognition =
        new SpeechRecognition();

    recognition.lang = "en-US";

    recognition.start();

    recognition.onresult = function(event) {

        const transcript =
            event.results[0][0].transcript;

        document.getElementById("codeInput").value =
            transcript;
    };
}

document
    .getElementById("voiceBtn")
    .addEventListener("click", startVoiceInput);
```
