import io
from fastapi import params, responses
import numpy as np
from numpy.testing import assert_array_equal
import pandas as pd


def test_get_response_data(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ensemble_id = create_ensemble(experiment_id=experiment_id, responses=["FOPR"])

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
    response_name = "FOPR"
    # post responses with realization_index
    for id_real in data_df:
        resp = client.post(
            f"/ensembles/{ensemble_id}/records/{response_name}/matrix",
            data=data_df[id_real].to_csv().encode(),
            headers={"content-type": "text/csv"},
            params={"realization_index": id_real},
        )

    resp = client.get(f"/ensembles/{ensemble_id}/responses/{response_name}/data")
    stream = io.BytesIO(resp.content)
    response_df = pd.read_csv(stream, index_col=0, float_precision="round_trip")
    for id_real in data_df:
        assert_array_equal(
            response_df.loc[id_real].values, data_df[id_real].values.flatten()
        )


def test_get_response_data_with_nan(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ensemble_id = create_ensemble(experiment_id=experiment_id, responses=["FOPR"])

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
    # alter some columns, labels
    data_df[0].columns = ["A", "B", "C", "D", "E", "F", "G", "I"]
    data_df[1].columns = ["A", "B", "C", "D", "F", "G", "I", "J"]
    response_name = "FOPR"
    # post responses with realization_index
    for id_real in data_df:
        resp = client.post(
            f"/ensembles/{ensemble_id}/records/{response_name}/matrix",
            data=data_df[id_real].to_csv().encode(),
            headers={"content-type": "text/csv"},
            params={"realization_index": id_real},
        )

    resp = client.get(f"/ensembles/{ensemble_id}/responses/{response_name}/data")
    stream = io.BytesIO(resp.content)
    response_df = pd.read_csv(stream, index_col=0, float_precision="round_trip")
    assert_array_equal(
        ["A", "B", "C", "D", "E", "F", "G", "I", "J", "H"], response_df.columns
    )
    assert response_df.shape == (5, 10)
    assert response_df.isnull().values.any() == True
