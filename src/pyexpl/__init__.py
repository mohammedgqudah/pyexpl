from typing import TypeGuard, cast
from flask import Flask, redirect, render_template, request, abort, url_for
from flask.typing import ResponseReturnValue
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pyexpl.runners import RUNNERS
import json
import secrets


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class SharedSession(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    runners: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)


def is_list_of_runners(runners: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(runner, str) for runner in runners)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////var/lib/pyexpl/database.db"
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
    app.config["MAX_FORM_MEMORY_SIZE"] = 1 * 1024 * 1024

    db.init_app(app)
    with app.app_context():
        db.create_all()

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
            "exit_code": result.returncode,
        }

    @app.post("/share")
    def share():  # pyright: ignore[reportUnusedFunction]
        required = ["code", "runners"]
        for field in required:
            if field not in request.form or not request.form.get(field):
                return abort(400, f"form request is missing `{field}`.")

        try:
            runners = cast(object, json.loads(request.form["runners"]))
            if not isinstance(runners, list):
                return abort(400, "`runners` is not a list.")

            runners = cast(list[object], runners)
            if not is_list_of_runners(runners):
                return abort(400, "`runners` is not a list of runners.")
            for runner in runners:
                if runner not in RUNNERS:
                    return abort(400, f"unknown runner `{runner}`")
        except json.JSONDecodeError:
            return abort(400, "`runners` is not valid JSON.")

        # ignore typing: https://github.com/microsoft/pyright/issues/626
        share = SharedSession(
            id=secrets.token_urlsafe(20),  # pyright: ignore[reportCallIssue]
            runners=runners,  # pyright: ignore[reportCallIssue]
            code=request.form["code"],  # pyright: ignore[reportCallIssue]
        )
        db.session.add(share)
        db.session.commit()
        return redirect(url_for("view_share", id=share.id))

    @app.get("/share/<id>")
    def view_share(id: str):  # pyright: ignore[reportUnusedFunction]
        share = db.get_or_404(SharedSession, id)
        return render_template(
            "index.html", share_id=id, code=share.code, runners=share.runners
        )

    return app


def main():
    create_app().run(port=8000, debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
