from pyexpl import create_app
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner
import pytest


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(  # pyright: ignore[reportUnknownMemberType]
        {
            "TESTING": True,
        }
    )
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
    response = client.post("/run", data={"code": "1+1", "runner": "unknwon"})
    assert 400 == response.status_code
    assert "unsupported runner" in response.text


@pytest.mark.parametrize(
    "version",
    [
        "3.14",
        "3.13",
        "3.12",
        "3.11",
        "3.10",
        "3.9",
        "3.8",
    ],
)
def test_python_versions(client: FlaskClient, version: str):
    response = client.post(
        "/run",
        data={
            "code": """
import sys
print("version:", sys.version)
        """.strip(),
            "runner": f"python{version}",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert f"version: {version}" in data["stdout"]
    assert 0 == data["exit_code"]


def test_syntax_error(client: FlaskClient):
    response = client.post(
        "/run",
        data={
            "code": """
print("hello
        """.strip(),
            "runner": "python3.13",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert "SyntaxError: unterminated string literal" in data["stdout"]
    assert data["exit_code"] != 0


def test_print_to_stderr(client: FlaskClient):
    response = client.post(
        "/run",
        data={
            "code": """
import sys
print("printing to stderr", file=sys.stderr)
        """.strip(),
            "runner": "python3.13",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert "printing to stderr" in data["stdout"]
    assert data["exit_code"] == 0


def test_stdout_max_limit(client: FlaskClient):
    response = client.post(
        "/run",
        data={
            "code": """
while True:
    print("1" * 200, end="", flush=True)
        """.strip(),
            "runner": "python3.13",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert data["stdout"] == ("1" * 10000) + "\n[Output truncated]"
    assert data["exit_code"] == 143


def test_ruff_check(client: FlaskClient):
    expected_output = """E401 [*] Multiple imports on one line
 --> -:1:1
  |
1 | import os, sys
  | ^^^^^^^^^^^^^^
2 | print(sys.version)
3 | print(os.listdir("/"))
  |
help: Split imports

Found 1 error.
[*] 1 fixable with the `--fix` option.
"""

    response = client.post(
        "/run",
        data={
            "code": """
import os, sys
print(sys.version)
print(os.listdir("/"))
""".strip(),
            "runner": "ruff-check",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert data["stdout"] == expected_output
    assert data["exit_code"] == 0


def test_ruff_format(client: FlaskClient):
    expected_output = "print(1 + 1)\n"
    response = client.post(
        "/run",
        data={
            "code": """
print  (  1    +  1)
""".strip(),
            "runner": "ruff-format",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert data["stdout"] == expected_output
    assert data["exit_code"] == 0


def test_mypy(client: FlaskClient):
    expected_output = """<string>:2: error: Incompatible return value type (got "str", expected "int")  [return-value]
Found 1 error in 1 file (checked 1 source file)
"""

    response = client.post(
        "/run",
        data={
            "code": """
def add(a: int, b: int) -> int:
    return "lol" 
""".strip(),
            "runner": "mypy",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType, reportRedeclaration]
    assert 200 == response.status_code
    assert data["stdout"] == expected_output
    assert data["exit_code"] == 0

    response = client.post(
        "/run",
        data={
            "code": """
from dataclasses import dataclass
from typing import reveal_type

type Either[L, R] = Left[L] | Right[R]
@dataclass
class Left[L]:
    l: L
@dataclass
class Right[R]:
    r: R
""".strip(),
            "runner": "mypy",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert "Success: no issues found in 1 source file" in data["stdout"]
    assert data["exit_code"] == 0


def test_pyright(client: FlaskClient):
    response = client.post(
        "/run",
        data={
            "code": """
def add(a: int, b: int) -> int:
    return "lol" 
""".strip(),
            "runner": "pyright",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert (
        'error: Type "Literal[\'lol\']" is not assignable to return type "int"'
        in data["stdout"]
    )
    assert (
        '"Literal[\'lol\']" is not assignable to "int" (reportReturnType)'
        in data["stdout"]
    )
    assert data["exit_code"] == 0


def test_pyre(client: FlaskClient):
    response = client.post(
        "/run",
        data={
            "code": """
def add(a: int, b: int) -> int:
    return "lol" 
""".strip(),
            "runner": "pyre",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert (
        "Incompatible return type [7]: Expected `int` but got `str`" in data["stdout"]
    )
    assert data["exit_code"] == 0


def test_pytype(client: FlaskClient):
    response = client.post(
        "/run",
        data={
            "code": """
import os, sys
def add(a: int, b: int) -> int:
    return "lol" 
""".strip(),
            "runner": "pytype",
        },
    )

    data: dict[str, str] = response.json  # pyright: ignore[reportAssignmentType]
    assert 200 == response.status_code
    assert "in add: bad return type [bad-return-type]" in data["stdout"]
    assert "Expected: int" in data["stdout"]
    assert "Actually returned: str" in data["stdout"]
    assert data["exit_code"] == 0
