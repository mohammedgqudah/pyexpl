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
    assert 200 == response.status_code
    assert response.json is not None
    assert f"version: {version}" in response.json["stdout"]

def test_timeout(client: FlaskClient):
    response = client.post("/run", data={
        "code": """
import time
time.sleep(2)
print("--pyexpl--")
        """.strip(),
        "runner": f"python3.13"
    })
    assert 200 == response.status_code
    assert response.json is not None
    assert f"--pyexpl--" in response.json["stdout"]

    response = client.post("/run", data={
        "code": """
import time
time.sleep(10)
print("--pyexpl--")
        """.strip(),
        "runner": f"python3.13"
    })
    assert 200 == response.status_code
    assert response.json is not None
    assert f"--pyexpl--" in response.json["stdout"]
