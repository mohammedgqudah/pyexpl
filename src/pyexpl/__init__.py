from flask import Flask, render_template, request, abort
from flask.typing import ResponseReturnValue
from pyexpl.runners import RUNNERS


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():  # pyright: ignore[reportUnusedFunction]
        return render_template("index.html")

    @app.post("/run")
    def run() -> ResponseReturnValue:  # pyright: ignore[reportUnusedFunction]
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

    return app


def main():
    create_app().run(port=8000, debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
