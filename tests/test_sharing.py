from pyexpl import create_app
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner
import pytest
import json
import re


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
    response = client.post("/share")
    assert 400 == response.status_code
    assert "form request is missing `code`" in response.text

    response = client.post("/share", data={"code": "1+1"})
    assert 400 == response.status_code
    assert "form request is missing `runners`" in response.text


def test_invalid_runner(client: FlaskClient):
    response = client.post(
        "/share", data={"code": "1+1", "runners": json.dumps(["invalid"])}
    )
    assert 400 == response.status_code
    assert "unknown runner `invalid`" in response.text

    response = client.post("/share", data={"code": "1+1", "runners": "xyz"})
    assert 400 == response.status_code
    assert "not valid JSON" in response.text

    response = client.post(
        "/share", data={"code": "1+1", "runners": json.dumps({"key": "val"})}
    )
    assert 400 == response.status_code
    assert "not a list." in response.text

    response = client.post(
        "/share", data={"code": "1+1", "runners": json.dumps([1, 2, 3])}
    )
    assert 400 == response.status_code
    assert "not a list of runners." in response.text


def test_sharing(client: FlaskClient):
    response = client.post(
        "/share",
        data={
            "code": "print(1+1)",
            "runners": json.dumps(["python3-13", "python3-14"]),
        },
    )
    assert 302 == response.status_code
    match = re.match(r"\/share\/(?P<share_id>.+)", response.location)
    assert match is not None

    response = client.get(response.location)
    assert match.group("share_id") in response.text
    assert "print(1+1)" in response.text
    assert '["python3-13", "python3-14"]' in response.text
