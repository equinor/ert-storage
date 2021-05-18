import random
import uuid
import io
from fastapi import params
import numpy as np
from numpy.testing import assert_equal
import pandas as pd


GET_UNIQUE_RESPONSES = """\
query($id: ID!) {
  ensemble(id: $id) {
    uniqueResponses {
      name
    }
  }
}
"""

GET_ALL_RESPONSES = """\
query($id: ID!) {
  ensemble(id: $id) {
    responses {
      name
      realizationIndex
    }
  }
}
"""


def test_get_gql_response(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ensemble_id = create_ensemble(experiment_id=experiment_id)

    # 5 realizations of 8 values each for FOPR
    matrices = np.random.rand(5, 8)

    data_df = {
        id_real: pd.DataFrame(
            [matrix],
            index=[f"{id_real}"],
            columns=["A", "B", "C", "D", "E", "F", "G", "H"],
        )
        for id_real, matrix in enumerate(matrices)
    }

    for id_real in data_df:
        client.post(
            f"/ensembles/{ensemble_id}/records/FOPR/matrix",
            data=data_df[id_real].to_csv().encode(),
            headers={"content-type": "application/x-dataframe"},
            params=dict(realization_index=id_real, record_class="response"),
        )

    r = client.gql_execute(GET_UNIQUE_RESPONSES, variable_values={"id": ensemble_id})
    assert r["data"]["ensemble"]["uniqueResponses"] == [{"name": "FOPR"}]
    r = client.gql_execute(GET_ALL_RESPONSES, variable_values={"id": ensemble_id})
    assert len(r["data"]["ensemble"]["responses"]) == 5
    for id_real, _ in enumerate(matrices):
        assert {"name": "FOPR", "realizationIndex": id_real} in r["data"]["ensemble"][
            "responses"
        ]
