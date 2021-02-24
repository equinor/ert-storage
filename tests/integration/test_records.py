import os
import pytest
import json
from fastapi.testclient import TestClient


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
        ("name", "[1, 2, 3, 4, 5]", True),
        ("name", "[5, 4, 3, 2, 1]", False),
        ("fail", "yes", False),
    ]

    # Post each of the record
    for name, data, should_succeed in records:
        failed = False
        try:
            resp = client.post(
                f"/ensembles/{ensemble_id}/records/{name}",
                data=data,
                headers={"RecordType": "float_vector"},
            )
            failed = resp.status_code != 200
        except Exception as exc:
            failed = True
        if should_succeed and failed:
            raise exc
        elif not should_succeed and not failed:
            raise AssertionError(
                f"Posting '{data}' to record '{name}' was expected to fail, but it succeeded"
            )

    # Compare list of records
    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == [
        rec[0] for rec in records if rec[2]  # name  # should_succeed
    ]

    # Compare getting each vector separately
    for name, data, should_succeed in records:
        if not should_succeed:
            continue
        resp = client.get(f"/ensembles/{ensemble_id}/records/{name}")
        assert resp.status_code == 200
        assert resp.json() == json.loads(data)


def _create_ensemble(client):
    resp = client.post("/ensembles", json={"parameters": PARAMETERS})
    return resp.json()["id"]
