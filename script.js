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

// Safely escape code before placing it into generated HTML.
function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

// Render the explanation response returned by Flask.
function renderExplanation(data) {
    const output = document.querySelector("#outputContent");
    const badge = document.querySelector("#detectedLanguage");
    const languages = data.selected_languages || ["English"];

    badge.textContent = data.language;

    const lines = data.lines.map((line) => {
        const explanations = languages.map((language) => {
            return `<p><strong>${language}:</strong> ${line.explanations[language]}</p>`;
        }).join("");

        return `
            <article class="line-card">
                <div class="line-code"><span>Line ${line.number}</span><code>${escapeHtml(line.code || "blank line")}</code></div>
                <div>${explanations}</div>
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

    output.className = "explanation-content";
    const summaries = languages.map((language) => {
        return `<p><strong>${language}:</strong> ${data.summaries[language]}</p>`;
    }).join("");
    const analogies = languages.map((language) => {
        return `<p><strong>${language}:</strong> ${data.analogies[language]}</p>`;
    }).join("");

    output.innerHTML = `
        <div class="summary-card">
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
}

// Send code to the Flask backend and show the AI-like explanation.
async function explainCode() {
    const codeInput = document.querySelector("#codeInput");
    const preference = document.querySelector("#languagePreference");
    const output = document.querySelector("#outputContent");

    output.className = "empty-state";
    output.textContent = "Thinking through your code...";

    const response = await fetch("/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            code: codeInput.value,
            preference: preference.value
        })
    });

    const data = await response.json();

    if (!response.ok) {
        output.textContent = data.error || "Something went wrong.";
        return;
    }

    renderExplanation(data);
}

// Render example buttons and wire them to the textarea.
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

    if (loadExampleBtn) {
        loadExampleBtn.addEventListener("click", () => {
            codeInput.value = examples[0].code;
            codeInput.focus();
        });
    }
}

// Store the user's theme choice in localStorage.
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

// Connect dashboard buttons after the page is ready.
document.addEventListener("DOMContentLoaded", () => {
    setupThemeToggle();
    setupExamples();

    const explainBtn = document.querySelector("#explainBtn");
    const clearBtn = document.querySelector("#clearBtn");
    const codeInput = document.querySelector("#codeInput");
    const output = document.querySelector("#outputContent");
    const badge = document.querySelector("#detectedLanguage");

    if (explainBtn) {
        explainBtn.addEventListener("click", explainCode);
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            codeInput.value = "";
            output.className = "empty-state";
            output.textContent = "Enter code and click Explain Code.";
            badge.textContent = "Waiting";
        });
    }
});
