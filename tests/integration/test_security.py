import pytest
from fastapi import status
from fastapi.testclient import TestClient
from ert_storage.security import DEFAULT_TOKEN


@pytest.fixture
def client(monkeypatch):
    """
    Separate TestClient fixture where we don't override the get_db dependency
    """
    # Disable environment variables
    monkeypatch.delenv("ERT_STORAGE_TOKEN", raising=False)

    from ert_storage.app import app

    return TestClient(app)


def test_auth_success(client, monkeypatch):
    resp = client.post("/ensembles", headers={"Token": DEFAULT_TOKEN})
    assert resp.status_code == status.HTTP_200_OK

    token = "sxbqRhLoFVbzmG4y"
    monkeypatch.setenv("ERT_STORAGE_TOKEN", token)
    resp = client.post("/ensembles", headers={"Token": token})
    assert resp.status_code == status.HTTP_200_OK


def test_auth_fail(client, monkeypatch):
    resp = client.post("/ensembles")
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    resp = client.post("/ensembles", headers={"Token": "Incorrect Token"})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    token = "sxbqRhLoFVbzmG4y"
    monkeypatch.setenv("ERT_STORAGE_TOKEN", token)
    resp = client.post("/ensembles", headers={"Token": "Still Incorrect Token"})
    assert resp.status_code == status.HTTP_403_FORBIDDEN
