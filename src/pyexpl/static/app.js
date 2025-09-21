var runners = ["python3-13"];

// setup split.js
Split(["#split-0", "#output-split-container"]);
var output_split = Split(["#output-python3-13"], {
	direction: "vertical",
});

// Add a new runner output pane.
// the runner will be requested whenever the editor is saved.
function newRunner(runner) {
	// FIXME: runners shouldn be HTML class-safe so that JS doesn't have
	// to work around that.
	runner = runner.replace(".", "-");
	if (runners.includes(runner)) {
		alert(`Runner ${runner} is already added.`);
		return;
	}
	runners.push(runner);
	const runner_id = `output-${runner}`;
	const container = document.getElementById('output-split-container');

	output_split.destroy(false, false);

	container.querySelectorAll('.gutter').forEach(g => g.remove());

	const panes = Array.from(container.children).filter(el => !el.classList.contains('gutter'));

	const outputPane = document.createElement('div');
	outputPane.id = runner_id;
	outputPane.classList += "output";
	outputPane.setAttribute('data-runner', runner);
	container.appendChild(outputPane);

	const paneSelectors = Array.from(container.children)
		.filter(el => !el.classList.contains('gutter'))
		.map(el => `#${el.id}`);

	output_split = Split(paneSelectors, {
		sizes: new Array(paneSelectors.length).fill(100 / paneSelectors.length),
		minSize: 100,
		gutterSize: 8,
		direction: 'vertical',
	});
}

// register on click for all runner buttons in the editor
document.querySelectorAll(".add-runner").forEach(button => {
	button.addEventListener("click", () => {
		const runner = button.getAttribute("data-runner");
		newRunner(runner);
		console.log("Added:", runner);
	});
});

// setup the code editor
let editor = ace.edit("editor");
ace.edit(editor, {
	mode: "ace/mode/python",
	selectionStyle: "text",
});
ace.require("ace/keybindings/vim");
editor.setKeyboardHandler("ace/keyboard/vim");
editor.setOptions({
	copyWithEmptySelection: true,
});
editor.setFontSize(18);
editor.setValue(`
import os, sys
print(sys.version)
print(os.listdir("/"))
`);

const Vim = ace.require("ace/keyboard/vim").CodeMirror.Vim;

let mapping = {
	"python3-13": "python3.13",
	"python3-12": "python3.12",
	"python3-11": "python3.11",
	"python3-10": "python3.10",
	"python3-9": "python3.9",
	"python3-8": "python3.8",
};

// send the editor content to the server for all registered runners
// and update the runner output accordingly.
function run() {
	for (idx in runners) {
		let runner = runners[idx];
		let output = document.getElementById(`output-${runner}`);
		let code = editor.getValue();
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
				output.innerText = r.stdout;
				if (r.exit_code != 0) {
					output.innerText += r.stderr;
				}
			})
			.catch((e) => {
				console.error(e);
				output.innerHTML = `failed (check dev console for details). ${e}`;
				console.log(
					`An error occured while running code via the runner ${runner}. Check the console for the error`,
				);
			});
	}
}
Vim.defineEx("write", "w", function (cm, input) {
	run();
});
document.getElementById('save-btn').addEventListener('click', run);
