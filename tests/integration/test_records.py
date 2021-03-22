import io
import pytest
import json
import random
import numpy as np
from fastapi import status


NUM_REALIZATIONS = 5
PARAMETERS = [
    [1.1, 2.1, 3.1],
    [1.2, 2.2, 3.2],
    [1.3, 2.3, 3.3],
    [1.4, 2.4, 3.4],
    [1.5, 2.5, 3.5],
]


def test_list(client):
    ensemble_id = _create_ensemble(client)

    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == {}

    client.post_check(f"/ensembles/{ensemble_id}/records/hello/matrix", data="[]")
    client.post_check(
        f"/ensembles/{ensemble_id}/records/foo/file",
        params=dict(realization_index=1),
        files={"file": ("foo.bar", io.BytesIO(), "foo/bar")},
    )
    client.post_check(
        f"/ensembles/{ensemble_id}/records/world/matrix",
        data="[]",
    )

    resp = client.get_check(f"/ensembles/{ensemble_id}/records")
    assert set(resp.json().keys()) == {"hello", "world", "foo"}


def test_parameters(client):
    ensemble_id = _create_ensemble(client, ["coeffs"])
    client.post(
        f"/ensembles/{ensemble_id}/records/coeffs/matrix",
        data=f"{PARAMETERS}",
    )

    resp = client.get_check(f"/ensembles/{ensemble_id}/parameters")
    assert resp.json() == ["coeffs"]

    resp = client.get_check(f"/ensembles/{ensemble_id}/records/coeffs")
    assert resp.json() == PARAMETERS

    for realization_index in range(NUM_REALIZATIONS):
        client.post_check(
            f"/ensembles/{ensemble_id}/records/indexed_coeffs/matrix",
            params=dict(realization_index=realization_index),
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
    ensemble_records = set(resp.json().keys())
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


def test_blocked_blob(client):

    ensemble_id = _create_ensemble(client)

    size = 12 * 1024 ** 2
    block_size = 4 * 1024 ** 2

    def _generate_blob_chunks():
        data = []
        with open("/dev/urandom", "rb") as file_handle:
            for _ in range(size // block_size):
                data.append(file_handle.read(block_size))
        return data

    client.post_check(
        f"/ensembles/{ensemble_id}/records/foo/blob",
    )
    chunks = _generate_blob_chunks()
    for i, chunk in enumerate(chunks):
        client.put_check(
            f"/ensembles/{ensemble_id}/records/foo/blob",
            params={"block_index": i},
            data=chunk,
        )

    client.patch_check(
        f"/ensembles/{ensemble_id}/records/foo/blob",
    )

    resp = client.get_check(
        f"/ensembles/{ensemble_id}/records/foo",
    )
    print(resp.content)
    assert b"".join(chunks) == resp.content


def _create_ensemble(client, parameters=[]):
    resp = client.post("/ensembles", json={"parameters": parameters})
    return resp.json()["id"]
