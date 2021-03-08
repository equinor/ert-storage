import os
import io
import pytest
import json
import random
import numpy as np
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import sessionmaker


NUM_REALIZATIONS = 5
PARAMETERS = [
    [1.1, 2.1, 3.1],
    [1.2, 2.2, 3.2],
    [1.3, 2.3, 3.3],
    [1.4, 2.4, 3.4],
    [1.5, 2.5, 3.5],
]


class _TestClient(TestClient):
    def get_check(self, *args, **kwargs):
        resp = self.get(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError
        return resp

    def post_check(self, *args, **kwargs):
        resp = self.post(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError
        return resp


@pytest.fixture
def client():
    from ert_storage.app import app
    from ert_storage.database import get_db, engine, IS_SQLITE, IS_POSTGRES
    from ert_storage.database_schema import Base

    if IS_SQLITE:
        Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=connection)

    async def override_get_db():
        db = TestSession()

        # Make PostgreSQL return float8 columns with highest precision. If we don't
        # do this, we may lose up to 3 of the least significant digits.
        if IS_POSTGRES:
            db.execute("SET extra_float_digits=3")
        try:
            yield db
            db.commit()
            db.close()
        except:
            db.rollback()
            db.close()
            raise

    app.dependency_overrides[get_db] = override_get_db
    yield _TestClient(app)

    # teardown: rollback database to before the test.
    # For debugging change rollback to commit.
    transaction.rollback()
    connection.close()


def test_list(client):
    ensemble_id = _create_ensemble(client)

    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == {
        "ensemble": {"consuming": {}, "producing": {}},
        "forward_model": {"consuming": {}, "producing": {}},
    }

    client.post_check(f"/ensembles/{ensemble_id}/records/hello/matrix", data="[]")
    client.post_check(
        f"/ensembles/{ensemble_id}/records/foo/file",
        params=dict(realization_index=1),
        files={"file": ("foo.bar", io.BytesIO(), "foo/bar")},
    )
    client.post_check(
        f"/ensembles/{ensemble_id}/records/world/matrix",
        params=dict(record_class="parameter"),
        data="[]",
    )

    resp = client.get_check(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == {
        "ensemble": {
            "producing": {"hello": "matrix"},
            "consuming": {"world": "matrix"},
        },
        "forward_model": {"producing": {"foo": "file"}, "consuming": {}},
    }


def test_parameters(client):
    ensemble_id = _create_ensemble(client)
    client.post(
        f"/ensembles/{ensemble_id}/records/coeffs/matrix",
        params=dict(record_class="parameter"),
        data=f"{PARAMETERS}",
    )

    resp = client.get_check(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == {
        "ensemble": {"consuming": {"coeffs": "matrix"}, "producing": {}},
        "forward_model": {"producing": {}, "consuming": {}},
    }

    resp = client.get_check(f"/ensembles/{ensemble_id}/records/coeffs")
    assert resp.json() == PARAMETERS

    for realization_index in range(NUM_REALIZATIONS):
        client.post_check(
            f"/ensembles/{ensemble_id}/records/indexed_coeffs/matrix",
            params=dict(record_class="parameter", realization_index=realization_index),
            data=f"{PARAMETERS[realization_index]}",
        )

    for realization_index in range(NUM_REALIZATIONS):
        resp = client.get_check(
            f"/ensembles/{ensemble_id}/records/indexed_coeffs",
            params=dict(realization_index=realization_index),
        )
        assert resp.json() == PARAMETERS[realization_index]


def test_matrix(client):
    ensemble_id = _create_ensemble(client)

    records = [
        ("name", "[1, 2, 3, 4, 5]", status.HTTP_200_OK),
        ("name", "[5, 4, 3, 2, 1]", status.HTTP_409_CONFLICT),
        ("mat2", "[[1, 2], [4, 5]]", status.HTTP_200_OK),
        ("fail", "yes", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]

    # Post each of the record
    for name, data, status_code in records:
        try:
            resp = client.post(
                f"/ensembles/{ensemble_id}/records/{name}/matrix",
                data=data,
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
            detail = resp.json()["detail"]
            if isinstance(detail, dict):
                # Pydantic validation errors will return a list. ERT Storage
                # returns a dictionary, so we only test for it.
                assert detail["ensemble_id"] == ensemble_id
                assert detail["name"] == name
                assert detail["error"] != ""

    # Compare list of records
    resp = client.get(f"/ensembles/{ensemble_id}/records")
    ensemble_records = set(resp.json()["ensemble"]["producing"])
    assert ensemble_records == {
        rec[0]
        for rec in records
        if rec[2] == status.HTTP_200_OK  # name  # should_succeed
    }


def test_missing_record_exception(client):
    ensemble_id = _create_ensemble(client)

    record_name = "coeffs_typo"
    resp = client.get(f"/ensembles/{ensemble_id}/records/{record_name}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    assert "detail" in resp.json()
    assert resp.json()["detail"]["ensemble_id"] == ensemble_id
    assert resp.json()["detail"]["name"] == "coeffs_typo"
    assert resp.json()["detail"]["error"] != ""


def test_ensemble_matrix(client):
    ensemble_id = _create_ensemble(client)

    matrix = np.random.rand(5, 8, 13)

    resp = client.post_check(
        f"/ensembles/{ensemble_id}/records/mat/matrix", json=matrix.tolist()
    )
    resp = client.get_check(f"/ensembles/{ensemble_id}/records/mat")

    assert resp.json() == matrix.tolist()


def test_ensemble_file(client):
    ensemble_id = _create_ensemble(client)

    with open("/dev/urandom", "rb") as f:
        data = f.read(random.randint(2 ** 16, 2 ** 24))
    client.post_check(
        f"/ensembles/{ensemble_id}/records/foo/file",
        files={"file": ("somefile", io.BytesIO(data), "foo/!@#$%^&*")},
    )
    resp = client.get_check(f"/ensembles/{ensemble_id}/records/foo")
    assert resp.status_code == 200
    assert resp.content == data


def test_forward_model_file(client):
    ensemble_id = _create_ensemble(client)

    with open("/dev/urandom", "rb") as f:
        data_a = f.read(random.randint(2 ** 16, 2 ** 24))
        data_b = f.read(random.randint(2 ** 16, 2 ** 24))
    index_a, index_b = random.sample(range(NUM_REALIZATIONS), 2)

    client.post_check(
        f"/ensembles/{ensemble_id}/records/foo/file?realization_index={index_a}",
        files={"file": ("first_file", io.BytesIO(data_a), "foo/bar")},
    )
    client.post_check(
        f"/ensembles/{ensemble_id}/records/foo/file?realization_index={index_b}",
        files={"file": ("second_file", io.BytesIO(data_b), "!@#$%^&*()")},
    )

    resp = client.get(f"/ensembles/{ensemble_id}/records/foo")
    assert resp.status_code == 404
    for realization_index in range(NUM_REALIZATIONS):
        resp = client.get(
            f"/ensembles/{ensemble_id}/records/foo?realization_index={realization_index}"
        )
        if realization_index == index_a:
            assert resp.status_code == 200
            assert resp.content == data_a
        elif realization_index == index_b:
            assert resp.status_code == 200
            assert resp.content == data_b
        else:
            assert resp.status_code == 404


def _create_ensemble(client):
    resp = client.post("/ensembles", json={"parameters": PARAMETERS})
    return resp.json()["id"]
