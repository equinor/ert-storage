import numpy as np
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

GET_ALL_RESPONSES_SUBSET = """\
query($id: ID!, $names: [String!]!) {
  ensemble(id: $id) {
    responses(names: $names) {
      name
      realizationIndex
    }
  }
}
"""

RESPONSE_NAMES = [
    "FOPR",
    "FOPT",
    "FGPT",
    "FGPR",
]


def test_get_gql_response(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ensemble_id = create_ensemble(experiment_id=experiment_id, responses=RESPONSE_NAMES)

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

    # post each realization of FOPR and FOPT as matrix
    for id_real in data_df:
        [
            client.post(
                f"/ensembles/{ensemble_id}/records/{resp_name}/matrix",
                data=data_df[id_real].to_csv().encode(),
                headers={"content-type": "application/x-dataframe"},
                params={"realization_index": id_real},
            )
            for resp_name in RESPONSE_NAMES
        ]

    r = client.gql_execute(GET_UNIQUE_RESPONSES, variable_values={"id": ensemble_id})
    for response in r["data"]["ensemble"]["uniqueResponses"]:
        assert response["name"] in RESPONSE_NAMES

    # retrieve all responses and realizations
    r = client.gql_execute(GET_ALL_RESPONSES, variable_values={"id": ensemble_id})

    assert len(r["data"]["ensemble"]["responses"]) == len(RESPONSE_NAMES) * 5
    for id_real, _ in enumerate(matrices):
        for response_name in RESPONSE_NAMES:
            assert {"name": response_name, "realizationIndex": id_real} in r["data"][
                "ensemble"
            ]["responses"]

    # use names attribute to retrieve only FOPR and FOPT realizations
    r = client.gql_execute(
        GET_ALL_RESPONSES_SUBSET,
        variable_values={"id": ensemble_id, "names": ["FOPR", "FOPT"]},
    )
    for id_real, _ in enumerate(matrices):
        for response_name in ["FOPR", "FOPT"]:
            assert {"name": response_name, "realizationIndex": id_real} in r["data"][
                "ensemble"
            ]["responses"]
