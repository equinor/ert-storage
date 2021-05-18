import json
import uuid
import numpy as np
from random import randint

GET_PRIORS = """\
query($experimentId: ID!) {
  experiment(id: $experimentId) {
    priors
  }
}
"""

GET_PRIOR_FOR_PARAMETERS = """\
query($ensembleId: ID!) {
  ensemble(id: $ensembleId) {
    parameters {
      id
      name
      prior
    }
  }
}
"""


def test_get_priors(client, create_experiment, make_random_priors):
    epriors = {rand_name(): prior.dict() for prior in make_random_priors(10)}
    eid = create_experiment(rand_name(), priors=epriors)
    r = client.gql_execute(GET_PRIORS, variable_values={"experimentId": eid})

    priors = json.loads(r["data"]["experiment"]["priors"])
    assert len(priors) == len(epriors)
    for name, prior in priors.items():
        assert epriors[name] == prior


def test_get_prior_for_parameters(client, create_ensemble, make_random_priors):
    NUM_PRIORS = 10
    NUM_PARAMS_W_PRIORS = 3
    NUM_PARAMS_WO_PRIORS = 4
    NUM_PARAMS = NUM_PARAMS_W_PRIORS + NUM_PARAMS_WO_PRIORS
    NUM_OTHER_RECORDS = 5

    # Sanity checking for our testing parameters
    assert NUM_PARAMS_W_PRIORS < NUM_PRIORS

    epriors = {rand_name(): prior.dict() for prior in make_random_priors(NUM_PRIORS)}
    eparams = [rand_name() for _ in range(NUM_PARAMS)]

    exp = client.post(
        "/experiments", json={"name": rand_name(), "priors": epriors}
    ).json()
    ensid = create_ensemble(exp["id"], parameters=eparams)
    print(exp)

    # Post parameters with priors
    param_to_prior = {}
    for param, prior, prior_val in zip(
        eparams, exp["priors"].values(), epriors.values()
    ):
        client.post(
            f"/ensembles/{ensid}/records/{param}/matrix",
            params={"prior_id": prior},
            json=np.random.rand(2, 3).tolist(),
        )
        param_to_prior[param] = prior_val

    # Post parameters without priors
    param_no_prior = set()
    for _ in range(NUM_PARAMS_WO_PRIORS):
        resp = client.post(
            f"/ensembles/{ensid}/records/{rand_name()}/matrix",
            json=np.random.rand(2, 3).tolist(),
        )
        param_no_prior.add(resp.json()["id"])

    # Post non-parameter records
    for _ in range(NUM_OTHER_RECORDS):
        client.post(
            f"/ensembles/{ensid}/records/{rand_name()}/matrix",
            json=np.random.rand(2, 3).tolist(),
        )

    resp = client.gql_execute(
        GET_PRIOR_FOR_PARAMETERS, variable_values={"ensembleId": ensid}
    )

    assert len(resp["data"]["ensemble"]["parameters"]) == NUM_PARAMS
    for param in resp["data"]["ensemble"]["parameters"]:
        if param["prior"] is not None:
            assert param["name"] in eparams
            assert json.loads(param["prior"]) == param_to_prior[param["name"]]
        else:
            assert param["id"] in param_no_prior


def rand_name():
    return str(uuid.uuid4())
