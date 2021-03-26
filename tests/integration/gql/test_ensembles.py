import uuid


GET_ENSEMBLE = """\
query($id: ID!) {
  ensemble(id: $id) {
    id
    inputs
  }
}
"""

CREATE_ENSEMBLE = """\
mutation create($experimentId: ID!, $params: [String]) {
  createEnsemble(experimentId: $experimentId, parameters: $params) {
    id
  }
}
"""


def test_get_ensemble(gql_client, simple_ensemble):
    eparams = [rand_name() for _ in range(3)]
    eid = simple_ensemble(eparams)
    r = gql_client.execute(GET_ENSEMBLE, variable_values={"id": eid})

    assert r["data"]["ensemble"]["id"] == str(eid)
    assert r["data"]["ensemble"]["inputs"] == eparams


def test_create_ensemble(gql_client, create_experiment):
    experiment_id = create_experiment(rand_name())
    eparams = [rand_name() for _ in range(8)]
    r = gql_client.execute(
        CREATE_ENSEMBLE,
        variable_values={"experimentId": experiment_id, "params": eparams},
    )
    eid = r["data"]["createEnsemble"]["id"]

    r = gql_client.execute(GET_ENSEMBLE, variable_values={"id": eid})

    assert r["data"]["ensemble"]["id"] == eid
    assert r["data"]["ensemble"]["inputs"] == eparams


def rand_name():
    return str(uuid.uuid4())
