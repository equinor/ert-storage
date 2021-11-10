import pytest
import json
from fastapi import status
from ert_storage.client.session import Session


def create_conn_config(base_url, auth):
    return json.dumps({"urls": [base_url], "authtoken": auth})


def test_healthcheck(server, base_url, monkeypatch):
    monkeypatch.setenv(
        "ERT_STORAGE_CONNECTION_STRING", create_conn_config(base_url, "")
    )
    with Session() as session:
        resp = session.get("/healthcheck")
        assert resp.status_code == status.HTTP_200_OK


def test_invalid_auth(server, base_url, monkeypatch):
    monkeypatch.setenv(
        "ERT_STORAGE_CONNECTION_STRING", create_conn_config(base_url, "")
    )
    with Session() as session:
        resp = session.get("/experiments")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_valid_auth(server, base_url, auth, monkeypatch):
    monkeypatch.setenv(
        "ERT_STORAGE_CONNECTION_STRING", create_conn_config(base_url, auth)
    )
    with Session() as session:
        resp = session.get("/experiments")
        assert resp.status_code == status.HTTP_200_OK
