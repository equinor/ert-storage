import io
from fastapi import params
import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd


OBSERVATION = (
    "FOPR",
    {"values": [1, 2, 3], "errors": [0.1, 0.2, 0.3], "x_axis": ["C", "E", "H"]},
)


def test_misfits_with_labels(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ensemble_id = create_ensemble(experiment_id=experiment_id)
    # post observation
    name, obs = OBSERVATION
    obs_id = client.post(
        f"/experiments/{experiment_id}/observations",
        json=dict(
            name=name,
            values=obs["values"],
            errors=obs["errors"],
            x_axis=obs["x_axis"],
        ),
    ).json()["id"]

    # 5 realizations of 8 values each
    matrices = np.random.rand(5, 8)

    data_df = {
        id_real: pd.DataFrame(
            [matrix],
            index=[f"{id_real}"],
            columns=["A", "B", "C", "D", "E", "F", "G", "H"],
        )
        for id_real, matrix in enumerate(matrices)
    }

    # post responses with the corresponding observation
    for id_real in data_df:
        resp = client.post(
            f"/ensembles/{ensemble_id}/records/{name}/matrix",
            data=data_df[id_real].to_csv().encode(),
            headers={"content-type": "application/x-dataframe"},
            params=dict(realization_index=id_real),
        )
        client.post(
            f"/ensembles/{ensemble_id}/records/{name}/observations",
            json=[obs_id],
            params=dict(realization_index=id_real),
        )
    # get all realizations of the univariate misfits
    resp = client.get(
        "/compute/misfits",
        params=dict(ensemble_id=str(ensemble_id), response_name=name),
    )
    stream = io.BytesIO(resp.content)
    misfits_df = pd.read_csv(stream, index_col=0, float_precision="round_trip")
    assert misfits_df.shape == (5, 3)
    assert_array_equal(misfits_df.columns, obs["x_axis"])

    # get summary misfits for all realizations
    resp = client.get(
        "/compute/misfits",
        params=dict(
            ensemble_id=str(ensemble_id), response_name=name, summary_misfits=True
        ),
    )
    stream = io.BytesIO(resp.content)
    misfits_df = pd.read_csv(stream, index_col=0, float_precision="round_trip")
    assert misfits_df.shape == (5, 1)

    # get realization #4 univariate misfits
    resp = client.get(
        "/compute/misfits",
        params=dict(
            ensemble_id=str(ensemble_id), response_name=name, realization_index=4
        ),
    )
    stream = io.BytesIO(resp.content)
    misfits_df = pd.read_csv(stream, index_col=0, float_precision="round_trip")

    assert_array_equal(misfits_df.columns, obs["x_axis"])
    assert misfits_df.shape == (1, 3)
