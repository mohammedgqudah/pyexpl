const STORAGE_KEYS = {
  CODE: 'ace_editor_code',
  RUNNERS: 'selected_runners'
};

// default example shown when no code yet saved
const DEFAULT_EXAMPLE = `import os, sys
print(sys.version)
print(os.listdir("/"))
`;

let runners = [];
// split.js Split for runners
let output_split = null;

// Mapping used when sending runners to the server.
// TODO: the server runners should be className safe to simplify js logic.
const mapping = {
  "python3-14": "python3.14",
  "python3-13": "python3.13",
  "python3-12": "python3.12",
  "python3-11": "python3.11",
  "python3-10": "python3.10",
  "python3-9":  "python3.9",
  "python3-8":  "python3.8",
};

// outer split (editor | outputs)
Split(["#split-0", "#output-split-container"]); 

// Save current runners to local stoarge
function saveRunners() {
  localStorage.setItem(STORAGE_KEYS.RUNNERS, JSON.stringify(runners));
}

// Load runners from local storage (or return default)
function loadRunners() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.RUNNERS);
    if (!raw) return ["python3-14"];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) && arr.length ? arr : ["python3-14"];
  } catch {
    return ["python3-14"];
  }
}

// Rebuild vertical Split with current panes (called after add/remove)
//
// Note: I don't think Split.js supprots dynamically adding or removing splits
// so the only option is to rebuild it every time.
function rebuildOutputSplit() {
  const container = document.getElementById('output-split-container');

  // Destroy any existing Split so we can rebuild
  if (output_split) {
    output_split.destroy(false, false);
    output_split = null;
  }

  // remove old gutters inserted by Split.js
  container.querySelectorAll('.gutter').forEach(g => g.remove());

  const paneSelectors = Array.from(container.children)
    .filter(el => !el.classList.contains('gutter'))
    .map(el => `#${el.id}`);

  if (paneSelectors.length === 0) {
    return;
  }

  output_split = Split(paneSelectors, {
    sizes: new Array(paneSelectors.length).fill(100 / paneSelectors.length),
    minSize: 100,
    gutterSize: 8,
    direction: 'vertical',
  });
}

// Create a DOM output pane (without touching runners array)
// Used by newRunner() and initial restore from local storage.
function createOutputPane(runner) {
  const safeRunner = runner.replace(/\./g, "-");
  const runner_id = `output-${safeRunner}`;
  const container = document.getElementById('output-split-container');

  if (document.getElementById(runner_id)) return;

  const outputPane = document.createElement('div');
  outputPane.id = runner_id;
  outputPane.classList.add('output');
  outputPane.setAttribute('data-runner', safeRunner);

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.className = 'close-btn';
  closeBtn.addEventListener('click', () => {
    // Remove this pane
    const idx = runners.indexOf(safeRunner);
    if (idx !== -1) {
      runners.splice(idx, 1);
      saveRunners();
    }
    outputPane.remove();
    rebuildOutputSplit();
  });


  const content = document.createElement('pre');
  content.className = 'output-content';

  outputPane.appendChild(content);
  outputPane.appendChild(closeBtn);

  container.appendChild(outputPane);
}

function newRunner(runner) {
  runner = runner.replace(/\./g, "-");

  if (runners.includes(runner)) {
    alert(`Runner ${runner} is already added.`);
    return;
  }

  runners.push(runner);
  saveRunners();

  createOutputPane(runner);
  rebuildOutputSplit();
}

function ensurePanesForRunners() {
  runners.forEach(r => createOutputPane(r));
  rebuildOutputSplit();
}

// editor setup
let editor = ace.edit("editor");
ace.edit(editor, { selectionStyle: "text" });

editor.setTheme("ace/theme/tomorrow_night");
editor.session.setMode("ace/mode/python");
editor.setKeyboardHandler("ace/keyboard/vim");
editor.setShowPrintMargin(false);
editor.setFontSize(18);

const savedCode = localStorage.getItem(STORAGE_KEYS.CODE);
editor.setValue(savedCode !== null ? savedCode : DEFAULT_EXAMPLE, -1); // -1 keeps cursor at start

editor.session.on('change', () => {
    localStorage.setItem(STORAGE_KEYS.CODE, editor.getValue());
});

const Vim = ace.require("ace/keyboard/vim").CodeMirror.Vim;
Vim.defineEx("write", "w", function () { run(); });

document.querySelectorAll(".add-runner").forEach(button => {
  button.addEventListener("click", () => {
    const runner = button.getAttribute("data-runner");
    newRunner(runner);
    console.log("Added:", runner);
  });
});

runners = loadRunners();
ensurePanesForRunners();

// send the editor content to the server for all registered runners
// and update the runner output accordingly.
function run() {
  for (let idx in runners) {
    const runner = runners[idx];
    const pane = document.getElementById(`output-${runner}`);
    if (!pane) continue;

    const output = pane.querySelector('.output-content') || pane;
    const code = editor.getValue();

    const formData = new FormData();
    formData.append("code", code);
    formData.append("runner", mapping[runner] || runner);

    output.innerHTML = "<progress></progress>";

    fetch("/run", {
      method: "POST",
      body: formData,
    })
      .then((r) => r.json())
      .then((r) => {
        output.textContent = r.stdout ?? "";
      })
      .catch((e) => {
        console.error(e);
        output.innerHTML = `failed (check dev console for details). ${e}`;
        console.log(
          `An error occured while running code via the runner ${runner}. Check the console for details`
        );
      });
  }
}

document.getElementById('save-btn').addEventListener('click', run);
