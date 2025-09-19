from flask import Flask, render_template, request, abort
from flask.typing import ResponseReturnValue
from pyexpl.runners import RUNNERS

app = Flask(__name__)

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
        supported_runners_msg = "\n-".join(RUNNERS.keys())
        return abort(
            400,
            f"unsupported runner `{runner}`. supported runners are\n -{supported_runners_msg}",
        )

    result = RUNNERS[runner].run(code)

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
    }


def main():
    app.run(port=8000, debug=True)


if __name__ == "__main__":
    main()
