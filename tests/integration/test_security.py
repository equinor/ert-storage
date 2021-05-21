import pytest
from fastapi import status
from fastapi.testclient import TestClient
from ert_storage.security import DEFAULT_TOKEN


@pytest.fixture
def client(ert_storage_client, monkeypatch):
    """
    Simple rename of ert_storage_client -> client
    """
    return ert_storage_client


def test_auth_success(client, monkeypatch):
    resp = client.post(
        "/experiments", json={"name": "test"}, headers={"Token": DEFAULT_TOKEN}
    )

    token = "sxbqRhLoFVbzmG4y"
    monkeypatch.setenv("ERT_STORAGE_TOKEN", token)
    resp = client.post("/experiments", json={"name": "test"}, headers={"Token": token})


def test_auth_fail(client, monkeypatch):
    client.post(
        "/experiments",
        json={"name": "test"},
        check_status_code=status.HTTP_403_FORBIDDEN,
    )

    client.post(
        "/experiments",
        json={"name": "test"},
        headers={"Token": "Incorrect Token"},
        check_status_code=status.HTTP_403_FORBIDDEN,
    )

    token = "sxbqRhLoFVbzmG4y"
    monkeypatch.setenv("ERT_STORAGE_TOKEN", token)
    client.post(
        "/experiments",
        json={"name": "test"},
        headers={"Token": "Still Incorrect Token"},
        check_status_code=status.HTTP_403_FORBIDDEN,
    )
