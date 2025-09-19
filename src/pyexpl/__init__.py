from flask import Flask, render_template, request, abort
from flask.typing import ResponseReturnValue
import subprocess
import tempfile

RUNNERS = [
    "python3.13",
    "python3.12",
    "python3.11",
    "python3.10",
    "python3.9",
    "python3.8",
    "ruff-check",
    "ruff-format",
    "mypy",
]

app = Flask(__name__)


def nsjail(cmd: list[str]):
    return [
        "nsjail",
        "--quiet",
        "-C",
        "nsjail.cfg",
        "--",
        *cmd
    ]

@app.get("/")
def index():
    return render_template("index.html")




@app.post("/run")
def run() -> ResponseReturnValue:
    if "code" not in request.form:
        return abort(400, "form request is missing `code`.")
    if "runner" not in request.form:
        return abort(400, "form request is missing `runner`.")

    code = request.form["code"]
    runner = request.form["runner"]
    if runner not in RUNNERS:
        supported_runners_msg = "\n-".join(RUNNERS)
        return abort(
            400,
            f"unsupported runner `{runner}`. supported runners are\n {supported_runners_msg}",
        )

    if runner == "ruff-check":
        process = subprocess.run(
            ["uvx", "ruff", "check", "-"],
            capture_output=True,
            input=code,
            text=True,
        )
    elif runner == "ruff-format":
        process = subprocess.run(
            ["uvx", "ruff", "format", "-"],
            capture_output=True,
            input=code,
            text=True,
        )
    elif runner == "mypy":
        with tempfile.NamedTemporaryFile("w+") as f:
            _ = f.write(code)
            f.flush()
            process = subprocess.run(
                ["uvx", "mypy", str(f.name)],
                capture_output=True,
                input=code,
                text=True,
            )
    else:
        process = subprocess.run(
            nsjail(["/usr/bin/env", "uv", "run", "--python", runner, "--script", "-"]),
            capture_output=True,
            input=code,
            text=True,
        )

    return {
        "stdout": process.stdout,
        "stderr": process.stderr,
        "exit_code": process.returncode,
    }


def main():
    app.run(port=8000, debug=True)


if __name__ == "__main__":
    main()
