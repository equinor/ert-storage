import random
import uuid


GET_ENSEMBLE = """\
query($id: ID!) {
  ensemble(id: $id) {
    id
    size
    parameterNames
    activeRealizations
  }
}
"""

CREATE_ENSEMBLE = """\
mutation create($experimentId: ID!, $size: Int!, $activeRealizations: [Int], $params: [String]) {
  createEnsemble(experimentId: $experimentId, size: $size, activeRealizations: $activeRealizations, parameterNames: $params) {
    id
  }
}
"""


def test_get_ensemble(client, simple_ensemble):
    eparams = [rand_name() for _ in range(3)]
    eid = simple_ensemble(eparams)
    r = client.gql_execute(GET_ENSEMBLE, variable_values={"id": eid})

    assert r["data"]["ensemble"]["id"] == str(eid)
    assert r["data"]["ensemble"]["parameterNames"] == eparams
    assert r["data"]["ensemble"]["activeRealizations"] == []


def test_create_ensemble(client, create_experiment):
    experiment_id = create_experiment(rand_name())
    eparams = [rand_name() for _ in range(8)]

    ensemble_size = random.randint(0, 1000)
    r = client.gql_execute(
        CREATE_ENSEMBLE,
        variable_values={
            "experimentId": experiment_id,
            "size": ensemble_size,
            "params": eparams,
        },
    )
    eid = r["data"]["createEnsemble"]["id"]

    r = client.gql_execute(GET_ENSEMBLE, variable_values={"id": eid})

    assert r["data"]["ensemble"]["id"] == eid
    assert r["data"]["ensemble"]["parameterNames"] == eparams
    assert r["data"]["ensemble"]["size"] == ensemble_size
    assert r["data"]["ensemble"]["activeRealizations"] == list(range(ensemble_size))


def rand_name():
    return str(uuid.uuid4())
