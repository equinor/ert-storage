import io
import json
import random
import numpy as np
import itertools
import pytest
from fastapi import status


NUM_REALIZATIONS = 5
PARAMETERS = [
    [1.1, 2.1, 3.1],
    [1.2, 2.2, 3.2],
    [1.3, 2.3, 3.3],
    [1.4, 2.4, 3.4],
    [1.5, 2.5, 3.5],
]


def test_list(client, simple_ensemble):
    ensemble_id = simple_ensemble()

    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert resp.json() == {}

    client.post(f"/ensembles/{ensemble_id}/records/hello/matrix", data="[]")
    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file",
        params=dict(realization_index=1),
        files={"file": ("foo.bar", io.BytesIO(), "foo/bar")},
    )
    client.post(
        f"/ensembles/{ensemble_id}/records/world/matrix",
        data="[]",
    )

    resp = client.get(f"/ensembles/{ensemble_id}/records")
    assert set(resp.json().keys()) == {"hello", "world", "foo"}


def test_parameters(client, simple_ensemble):
    ensemble_id = simple_ensemble(["coeffs"])
    client.post(
        f"/ensembles/{ensemble_id}/records/coeffs/matrix",
        data=f"{PARAMETERS}",
    )

    resp = client.get(f"/ensembles/{ensemble_id}/parameters")
    assert resp.json() == ["coeffs"]

    resp = client.get(f"/ensembles/{ensemble_id}/records/coeffs")
    assert resp.json() == PARAMETERS

    for realization_index in range(NUM_REALIZATIONS):
        client.post(
            f"/ensembles/{ensemble_id}/records/indexed_coeffs/matrix",
            params=dict(realization_index=realization_index),
            data=f"{PARAMETERS[realization_index]}",
        )

    for realization_index in range(NUM_REALIZATIONS):
        resp = client.get(
            f"/ensembles/{ensemble_id}/records/indexed_coeffs",
            params=dict(realization_index=realization_index),
        )
        assert resp.json() == PARAMETERS[realization_index]


def test_matrix(client, simple_ensemble):
    ensemble_id = simple_ensemble()

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
                check_status_code=None,
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


def test_missing_record_exception(client, simple_ensemble):
    ensemble_id = simple_ensemble()

    record_name = "coeffs_typo"
    resp = client.get(
        f"/ensembles/{ensemble_id}/records/{record_name}", check_status_code=None
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    assert "detail" in resp.json()
    assert resp.json()["detail"]["ensemble_id"] == ensemble_id
    assert resp.json()["detail"]["name"] == "coeffs_typo"
    assert resp.json()["detail"]["error"] != ""


@pytest.mark.parametrize(
    "get,post", list(itertools.product(["json", "numpy"], repeat=2))
)
def test_ensemble_matrix_json(client, simple_ensemble, get, post):
    from numpy.lib.format import write_array, read_array

    ensemble_id = simple_ensemble()

    matrix = np.random.rand(5, 8, 13)

    # POST
    post_url = f"/ensembles/{ensemble_id}/records/mat/matrix"
    if post == "json":
        resp = client.post(post_url, json=matrix.tolist())
    elif post == "numpy":
        stream = io.BytesIO()
        write_array(stream, matrix)
        resp = client.post(
            post_url,
            data=stream.getvalue(),
            headers={"content-type": "application/x-numpy"},
        )
    else:
        raise NotImplementedError()

    # GET
    get_url = f"/ensembles/{ensemble_id}/records/mat"
    if get == "json":
        resp = client.get(f"/ensembles/{ensemble_id}/records/mat")
        assert resp.json() == matrix.tolist()
    elif get == "numpy":
        resp = client.get(
            f"/ensembles/{ensemble_id}/records/mat",
            headers={"accept": "application/x-numpy"},
        )
        stream = io.BytesIO(resp.content)
        assert (read_array(stream) == matrix).all()
    else:
        raise NotImplementedError()


def test_ensemble_matrix_dataframe(client, simple_ensemble):
    from numpy.testing import assert_array_equal

    ensemble_id = simple_ensemble()
    matrix = np.random.rand(8, 5)
    labels = [
        ["north", "south", "east", "west", "up"],
        ["A", "B", "C", "D", "E", "F", "G", "H"],
    ]
    # POST
    post_url = f"/ensembles/{ensemble_id}/records/mat/matrix"
    import pandas as pd

    data = pd.DataFrame(matrix)
    data.columns = labels[0]
    data.index = labels[1]
    resp = client.post(
        post_url,
        data=data.to_csv().encode(),
        headers={"content-type": "application/x-dataframe"},
    )

    # GET
    get_url = f"/ensembles/{ensemble_id}/records/mat"
    resp = client.get(
        f"/ensembles/{ensemble_id}/records/mat",
        headers={"accept": "application/x-dataframe"},
    )
    stream = io.BytesIO(resp.content)
    df = pd.read_csv(stream, index_col=0, float_precision="round_trip")

    assert_array_equal(df.values, data.values)
    assert_array_equal(df.columns.values, data.columns.values)
    assert_array_equal(df.index.values, data.index.values)


def test_ensemble_file(client, simple_ensemble):
    ensemble_id = simple_ensemble()

    with open("/dev/urandom", "rb") as f:
        data = f.read(random.randint(2 ** 16, 2 ** 24))
    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file",
        files={"file": ("somefile", io.BytesIO(data), "foo/!@#$%^&*")},
    )
    resp = client.get(f"/ensembles/{ensemble_id}/records/foo")
    assert resp.status_code == 200
    assert resp.content == data


def test_forward_model_file(client, simple_ensemble):
    ensemble_id = simple_ensemble()

    with open("/dev/urandom", "rb") as f:
        data_a = f.read(random.randint(2 ** 16, 2 ** 24))
        data_b = f.read(random.randint(2 ** 16, 2 ** 24))
    index_a, index_b = random.sample(range(NUM_REALIZATIONS), 2)

    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file?realization_index={index_a}",
        files={"file": ("first_file", io.BytesIO(data_a), "foo/bar")},
    )
    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file?realization_index={index_b}",
        files={"file": ("second_file", io.BytesIO(data_b), "!@#$%^&*()")},
    )

    resp = client.get(f"/ensembles/{ensemble_id}/records/foo", check_status_code=None)
    assert resp.status_code == 404
    for realization_index in range(NUM_REALIZATIONS):
        resp = client.get(
            f"/ensembles/{ensemble_id}/records/foo?realization_index={realization_index}",
            check_status_code=None,
        )
        if realization_index == index_a:
            assert resp.status_code == 200
            assert resp.content == data_a
        elif realization_index == index_b:
            assert resp.status_code == 200
            assert resp.content == data_b
        else:
            assert resp.status_code == 404


def test_blocked_blob(client, simple_ensemble):

    ensemble_id = simple_ensemble()

    size = 12 * 1024 ** 2
    block_size = 4 * 1024 ** 2

    def _generate_blob_chunks():
        data = []
        with open("/dev/urandom", "rb") as file_handle:
            for _ in range(size // block_size):
                data.append(file_handle.read(block_size))
        return data

    client.post(
        f"/ensembles/{ensemble_id}/records/foo/blob",
    )
    chunks = _generate_blob_chunks()
    for i, chunk in enumerate(chunks):
        client.put(
            f"/ensembles/{ensemble_id}/records/foo/blob",
            params={"block_index": i},
            data=chunk,
        )

    client.patch(
        f"/ensembles/{ensemble_id}/records/foo/blob",
    )

    resp = client.get(
        f"/ensembles/{ensemble_id}/records/foo",
    )
    assert b"".join(chunks) == resp.content


def test_responses(client, simple_ensemble):
    ensemble_id = simple_ensemble()
    records = [
        ("rec1", "[1, 2, 3, 4, 5]", "other"),
        ("rec2", "[5, 4, 3, 2, 1]", "parameter"),
        ("rec3", "[[1, 2], [4, 5]]", "response"),
        ("rec4", "[[1, 2], [4, 5]]", None),
    ]
    for name, data, record_class in records:
        client.post(
            f"/ensembles/{ensemble_id}/records/{name}/matrix",
            data=data,
            params={
                "record_class": record_class,
            },
        )

    responses = client.get(f"/ensembles/{ensemble_id}/responses").json()
    assert len(responses) == 1
    data = client.get(f"/records/{responses['rec3']['id']}/data").json()
    assert data == [[1, 2], [4, 5]]
