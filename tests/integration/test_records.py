import io
import json
import random
import itertools
import numpy as np
import pandas as pd
import pytest
from fastapi import status
from numpy.testing import assert_array_equal


NUM_REALIZATIONS = 5
PARAMETERS = [
    [1.1, 2.1, 3.1],
    [1.2, 2.2, 3.2],
    [1.3, 2.3, 3.3],
    [1.4, 2.4, 3.4],
    [1.5, 2.5, 3.5],
]


def test_list(client, simple_ensemble):
    ensemble_id = simple_ensemble(size=2)

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


def test_ensemble_size_out_of_bounds(client, simple_ensemble):
    ensemble_id = simple_ensemble(size=1)

    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file",
        params=dict(realization_index=1),
        files={"file": ("foo.bar", io.BytesIO(), "foo/bar")},
        check_status_code=status.HTTP_417_EXPECTATION_FAILED,
    )

    ensemble_id = simple_ensemble(size=4, active_realizations=[0, 2])

    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file",
        params=dict(realization_index=1),
        files={"file": ("foo.bar", io.BytesIO(), "foo/bar")},
        check_status_code=status.HTTP_417_EXPECTATION_FAILED,
    )

    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file",
        params=dict(realization_index=2),
        files={"file": ("foo.bar", io.BytesIO(), "foo/bar")},
        check_status_code=status.HTTP_200_OK,
    )


def test_parameters(client, simple_ensemble):
    ensemble_id = simple_ensemble(["coeffs"], size=5)
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


def test_ensemble_wide_parameters(client, simple_ensemble):
    ensemble_id = simple_ensemble(["coeffs"])
    client.post(
        f"/ensembles/{ensemble_id}/records/coeffs/matrix",
        data=f"{PARAMETERS}",
    )

    # Fetch as ensemble-wide parameters
    resp = client.get(f"/ensembles/{ensemble_id}/records/coeffs")
    assert resp.json() == PARAMETERS

    # Fetch with realization_index
    for index, param in enumerate(PARAMETERS):
        resp = client.get(
            f"/ensembles/{ensemble_id}/records/coeffs",
            params={"realization_index": index},
        )
        assert resp.json() == param


@pytest.mark.parametrize("mimetype", ["application/x-parquet", "text/csv"])
def test_ensemble_wide_parameters_dataframe(client, simple_ensemble, mimetype):
    ensemble_id = simple_ensemble(["coeffs"])
    matrix = np.random.rand(8, 5)
    labels = [
        ["north", "south", "east", "west", "up"],
        ["A", "B", "C", "D", "E", "F", "G", "H"],
    ]

    data = pd.DataFrame(matrix)
    data.columns = labels[0]
    data.index = labels[1]

    if mimetype == "application/x-parquet":
        stream = io.BytesIO()
        data.to_parquet(stream)
        data_formatted = stream.getvalue()
    else:
        data_formatted = data.to_csv()

    client.post(
        f"/ensembles/{ensemble_id}/records/coeffs/matrix",
        data=data_formatted,
        headers={"content-type": mimetype},
    )

    # Fetch as ensemble-wide parameters
    resp = client.get(
        f"/ensembles/{ensemble_id}/records/coeffs",
        headers={"accept": mimetype},
    )
    if mimetype == "application/x-parquet":
        stream = io.BytesIO()
        data.to_parquet(stream)
        assert resp.content == stream.getvalue()
    else:
        assert resp.content == data.to_csv().encode()

    # Fetch with realization_index
    for index, param in enumerate(data.iterrows()):
        resp = client.get(
            f"/ensembles/{ensemble_id}/records/coeffs",
            params={"realization_index": index},
            headers={"accept": mimetype},
        )

        # param[1] is a pd.Series type, which is converted to DataFrame and transposed
        expect_param = param[1].to_frame().T

        if mimetype == "application/x-parquet":
            actual_param = pd.read_parquet(io.BytesIO(resp.content))
        else:
            actual_param = pd.read_csv(
                io.BytesIO(resp.content), index_col=0, float_precision="round_trip"
            )

        assert [index] == actual_param.index

        # The index of the returned parameter vector is the realization index, not labels[1].
        assert_array_equal([index], actual_param.index)
        assert_array_equal(expect_param.columns, actual_param.columns)
        assert_array_equal(expect_param.values, actual_param.values)


def test_ensemble_wide_parameters_1d(client, simple_ensemble):
    """
    Ensemble-wide parameter records must be at least 2-dimensional, where the
    first axis is the realization index
    """
    ensemble_id = simple_ensemble(["coeffs"])
    client.post(
        f"/ensembles/{ensemble_id}/records/coeffs/matrix",
        json=[1, 2, 3, 4, 5],
        check_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


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


@pytest.mark.parametrize("mimetype", ["application/x-parquet", "text/csv"])
def test_ensemble_matrix_dataframe(client, simple_ensemble, mimetype):
    ensemble_id = simple_ensemble()
    matrix = np.random.rand(8, 5)
    labels = [
        ["north", "south", "east", "west", "up"],
        ["A", "B", "C", "D", "E", "F", "G", "H"],
    ]
    # POST
    post_url = f"/ensembles/{ensemble_id}/records/mat/matrix"

    data = pd.DataFrame(matrix)
    data.columns = labels[0]
    data.index = labels[1]

    if mimetype == "application/x-parquet":
        stream = io.BytesIO()
        data.to_parquet(stream)
        data_formatted = stream.getvalue()
    else:
        data_formatted = data.to_csv()

    resp = client.post(
        post_url,
        data=data_formatted,
        headers={"content-type": mimetype},
    )

    # GET
    get_url = f"/ensembles/{ensemble_id}/records/mat"
    resp = client.get(
        f"/ensembles/{ensemble_id}/records/mat",
        headers={"accept": mimetype},
    )
    stream = io.BytesIO(resp.content)

    if mimetype == "application/x-parquet":
        df = pd.read_parquet(stream)
    else:
        df = pd.read_csv(stream, index_col=0, float_precision="round_trip")

    assert_array_equal(df.values, data.values)
    assert_array_equal(df.columns.values, data.columns.values)
    assert_array_equal(df.index.values, data.index.values)


@pytest.mark.parametrize(
    "labels",
    [
        [
            ["north", "south", "east", "west", "up"],
            ["1.0", "2.0", "3.0", "4.0", "5.0", "6.0", "7.0", "8.0"],
        ],
        [
            ["A", "B", "C", "D", "E"],
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        ],
        [
            ["A", "B", "C", "D", "E"],
            [1, 2, 3, 4, 5, 6, 7, 8],
        ],
        [
            ["A", "B", "C", "D", "E"],
            [
                np.datetime64("2020-01-01"),
                np.datetime64("2020-01-02"),
                np.datetime64("2020-01-03"),
                np.datetime64("2020-01-04"),
                np.datetime64("2020-01-05"),
                np.datetime64("2020-01-06"),
                np.datetime64("2020-01-07"),
                np.datetime64("2020-01-08"),
            ],
        ],
    ],
)
def test_ensemble_dataframe_labels(client, simple_ensemble, labels):
    mimetype = "application/x-parquet"
    ensemble_id = simple_ensemble()
    matrix = np.random.rand(8, 5)
    # POST
    post_url = f"/ensembles/{ensemble_id}/records/mat/matrix"

    data = pd.DataFrame(matrix)
    data.columns = labels[0]
    data.index = labels[1]
    stream = io.BytesIO()
    data.to_parquet(stream)
    resp = client.post(
        post_url,
        data=stream.getvalue(),
        headers={"content-type": mimetype},
    )

    # GET
    get_url = f"/ensembles/{ensemble_id}/records/mat"
    resp = client.get(
        f"/ensembles/{ensemble_id}/records/mat",
        headers={"accept": mimetype},
    )
    stream = io.BytesIO(resp.content)
    df = pd.read_parquet(stream)
    assert_array_equal(df.values, data.values)
    assert type(data.index) == type(df.index)
    assert type(data.columns) == type(df.columns)


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
    ensemble_id = simple_ensemble(size=5)

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


def test_chunked_blob(client, simple_ensemble):

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


def test_chunked_blob_out_of_order(client, simple_ensemble):
    ensemble_id = simple_ensemble()
    chunks = [
        (1, b"b"),
        (0, b"a"),
        (2, b"c"),
    ]

    client.post(
        f"/ensembles/{ensemble_id}/records/foo/blob",
    )
    for i, chunk in chunks:
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
    assert resp.content == b"abc"


def test_responses(client, simple_ensemble):
    ensemble_id = simple_ensemble(parameters=["rec2"], responses=["rec3"])
    records = [
        ("rec1", "[1, 2, 3, 4, 5]"),
        ("rec2", "[[4, 3, 2, 1]]"),
        ("rec3", "[[1, 2], [4, 5]]"),
        ("rec4", "[[1, 2], [4, 5]]"),
    ]
    for name, data in records:
        client.post(
            f"/ensembles/{ensemble_id}/records/{name}/matrix",
            data=data,
        )

    responses = client.get(f"/ensembles/{ensemble_id}/responses").json()
    assert len(responses) == 1
    data = client.get(f"/records/{responses['rec3']['id']}/data").json()
    assert data == [[1, 2], [4, 5]]


def test_fetch_matrix_ensemble_record_by_realization(client, simple_ensemble):
    ensemble_id = simple_ensemble(parameters=[], responses=["polynomial_output"])
    client.post(
        url=f"/ensembles/{ensemble_id}/records/polynomial_output/matrix",
        headers={"content-type": "text/csv"},
        data=b",0,1\n0,1.0,3.0\n1,1.0,1.0\n2,2.0,4.0\n3,3.0,1.0\n4,5.0,5.0\n",
    )
    resp = client.get(
        url=f"/ensembles/{ensemble_id}/records/polynomial_output",
        params={"realization_index": 0},
    )
    real_0 = resp.json()
    assert real_0 == [1.0, 3.0]

    resp = client.get(
        url=f"/ensembles/{ensemble_id}/records/polynomial_output",
        params={"realization_index": 4},
    )
    real_4 = resp.json()
    assert real_4 == [5.0, 5.0]
