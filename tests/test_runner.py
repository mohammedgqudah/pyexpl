from typing import Any
from pyexpl import create_app
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner
import pytest

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({  # pyright: ignore[reportUnknownMemberType]
        "TESTING": True,
    })
    yield app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture()
def runner(app: Flask) -> FlaskCliRunner:
    return app.test_cli_runner()


def test_missing_form_data(client: FlaskClient):
    response = client.post("/run")
    assert 400 == response.status_code
    assert "form request is missing `code`" in response.text

    response = client.post("/run", data={"code": "1+1"})
    assert 400 == response.status_code
    assert "form request is missing `runner`" in response.text

def test_unknown_runner(client: FlaskClient):
    response = client.post("/run", data={
        "code": "1+1",
        "runner": "unknwon"
    })
    assert 400 == response.status_code
    assert "unsupported runner" in response.text

@pytest.mark.parametrize("version", [
    "3.13",
    "3.12",
    "3.11",
    "3.10",
    "3.9",
    "3.8",
])
def test_python_versions(client: FlaskClient, version: str):
    response = client.post("/run", data={
        "code": """
import sys
print("version:", sys.version)
        """.strip(),
        "runner": f"python{version}"
    })

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert f"version: {version}" in data["stdout"]
    assert 0 == data["exit_code"]
    assert data["stderr"] == ""

def test_syntax_error(client: FlaskClient):
    response = client.post("/run", data={
        "code": """
print("hello
        """.strip(),
        "runner": f"python3.13"
    })

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert "SyntaxError: unterminated string literal" in data["stderr"]
    assert data["stdout"] == ""
    assert data['exit_code'] != 0

def test_print_to_stderr(client: FlaskClient):
    response = client.post("/run", data={
        "code": """
import sys
print("printing to stderr", file=sys.stderr)
        """.strip(),
        "runner": f"python3.13"
    })

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert "printing to stderr" in data["stderr"]  
    assert data["stdout"] == ""
    assert data['exit_code'] == 0
