import os
import pytest
import json
from fastapi.testclient import TestClient
from fastapi import status


PARAMETERS = [
    [1.1, 2.1, 3.1],
    [1.2, 2.2, 3.2],
    [1.3, 2.3, 3.3],
    [1.4, 2.4, 3.4],
    [1.5, 2.5, 3.5],
]


@pytest.fixture(scope="module")
def client():
    from ert_storage.app import app

    return TestClient(app)


def test_list(client):
    ensemble_id = _create_ensemble(client)

    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == []

    client.post(f"/ensembles/{ensemble_id}/records/hello", data="{}")
    client.post(f"/ensembles/{ensemble_id}/records/world", data="{}")

    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == ["hello", "world"]


def test_parameters(client):
    ensemble_id = _create_ensemble(client)
    client.post(
        f"/ensembles/{ensemble_id}/records/coeffs", headers={"RecordType": "parameters"}
    )

    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == ["coeffs"]

    resp = client.get(f"/ensembles/{ensemble_id}/records/coeffs")
    assert resp.json() == PARAMETERS

    for realization_index in range(5):
        resp = client.get(
            f"/ensembles/{ensemble_id}/records/coeffs/{realization_index}"
        )
        assert resp.json() == PARAMETERS[realization_index]


def test_float_vector(client):
    ensemble_id = _create_ensemble(client)

    records = [
        ("name", "[1, 2, 3, 4, 5]", status.HTTP_200_OK),
        ("name", "[5, 4, 3, 2, 1]", status.HTTP_409_CONFLICT),
        ("fail", "yes", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE),
    ]

    # Post each of the record
    for name, data, status_code in records:
        try:
            resp = client.post(
                f"/ensembles/{ensemble_id}/records/{name}",
                data=data,
                headers={"RecordType": "float_vector"},
            )
        except Exception:
            if status_code == status.HTTP_200_OK:
                raise AssertionError(
                    f"Posting '{data}' to record '{name}' was expected to succeed, but it failed"
                )

        assert resp.status_code == status_code
        if status_code == status.HTTP_200_OK:
            resp = client.get(f"/ensembles/{ensemble_id}/records/{name}")
            assert resp.json() == json.loads(data)
        else:
            assert "detail" in resp.json()
            assert resp.json()["detail"]["ensemble_id"] == ensemble_id
            assert resp.json()["detail"]["name"] == name
            assert resp.json()["detail"]["error"] != ""

    # Compare list of records
    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == [
        rec[0]
        for rec in records
        if rec[2] == status.HTTP_200_OK  # name  # should_succeed
    ]


def test_missing_record_exception(client):
    ensemble_id = _create_ensemble(client)

    record_name = "coeffs_typo"
    resp = client.get(f"/ensembles/{ensemble_id}/records/{record_name}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    assert "detail" in resp.json()
    assert resp.json()["detail"]["ensemble_id"] == ensemble_id
    assert resp.json()["detail"]["name"] == "coeffs_typo"
    assert resp.json()["detail"]["error"] != ""


def _create_ensemble(client):
    resp = client.post("/ensembles", json={"parameters": PARAMETERS})
    return resp.json()["id"]
