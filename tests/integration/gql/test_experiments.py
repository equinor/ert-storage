import uuid


GET_EXPERIMENT = """\
query($id: ID!) {
  experiment(id: $id) {
    name
    id
    ensembles {
      id
      parameterNames
    }
  }
}
"""

GET_EXPERIMENTS = """\
{
  experiments {
    id
    name
  }
}
"""

CREATE_EXPERIMENT = """\
mutation($name: String) {
  createExperiment(name: $name) {
    name
    id
  }
}
"""


CREATE_EXPERIMENT_WITH_ENSEMBLE = """\
mutation($name: String, $size: Int!, $params: [String!]) {
  createExperiment(name: $name) {
    id
    createEnsemble(size: $size, parameterNames: $params) {
      id
    }
  }
}
"""


def test_get_single_experiment(client, create_experiment):
    ename = rand_name()
    eid = create_experiment(ename)

    r = client.gql_execute(
        GET_EXPERIMENT,
        variable_values={"id": eid},
    )
    assert r["data"]["experiment"]["id"] == str(eid)
    assert r["data"]["experiment"]["name"] == ename


def test_get_list_experiments(client, create_experiment):
    enames = [rand_name() for _ in range(5)]
    eids = [str(create_experiment(ename)) for ename in enames]

    r = client.gql_execute(GET_EXPERIMENTS)
    actual_eids = {e["id"] for e in r["data"]["experiments"]}
    actual_enames = {e["name"] for e in r["data"]["experiments"]}

    assert len(r["data"]["experiments"]) >= 5
    assert set(eids) <= actual_eids
    assert set(enames) <= actual_enames


def test_create_experiment(client):
    ename = rand_name()
    r = client.gql_execute(CREATE_EXPERIMENT, variable_values={"name": ename})

    eid = r["data"]["createExperiment"]["id"]
    r = client.gql_execute(
        GET_EXPERIMENT,
        variable_values={"id": eid},
    )
    assert r["data"]["experiment"]["id"] == eid
    assert r["data"]["experiment"]["name"] == ename


def test_create_experiment_with_ensemble(client):
    ename = rand_name()
    eparams = [rand_name() for _ in range(5)]
    r = client.gql_execute(
        CREATE_EXPERIMENT_WITH_ENSEMBLE,
        variable_values={"name": ename, "size": 0, "params": eparams},
    )

    eid = r["data"]["createExperiment"]["id"]
    r = client.gql_execute(
        GET_EXPERIMENT,
        variable_values={"id": eid},
    )
    assert r["data"]["experiment"]["id"] == eid
    assert r["data"]["experiment"]["name"] == ename
    assert len(r["data"]["experiment"]["ensembles"]) == 1
    assert r["data"]["experiment"]["ensembles"][0]["parameterNames"] == eparams


def rand_name():
    return str(uuid.uuid4())
