import numpy as np
import random
from uuid import uuid4
from fastapi import status
from ert_storage import json_schema as js


def test_get_multiple_experiments(client, create_experiment):
    expected_experiments = {"test1", "test2", "test3"}
    for name in expected_experiments:
        create_experiment(name)

    docs = [
        exp
        for exp in client.get("/experiments").json()
        if exp["name"] in expected_experiments
    ]

    assert expected_experiments == {exp["name"] for exp in docs}
    assert all(exp["ensemble_ids"] == [] for exp in docs)

    # get experiments one by one
    experiment_ids = {exp["id"]: exp["name"] for exp in docs}
    for exp_id in experiment_ids:
        assert (
            client.get(f"/experiments/{exp_id}").json()["name"]
            == experiment_ids[exp_id]
        )


def test_post_prior_experiment(client, make_prior):
    prior = make_prior()

    experiment_id = client.post(
        "/experiments", json={"name": "test", "priors": {"testpri": prior.dict()}}
    ).json()["id"]

    priors = client.get(f"/experiments/{experiment_id}").json()["priors"]
    assert len(priors) == 1
    assert priors["testpri"] == prior


def test_post_multiple_priors_experiment(client, make_random_priors):
    priors = {random_name(): prior.dict() for prior in make_random_priors(10)}

    experiment_id = client.post(
        "/experiments", json={"name": "footest", "priors": priors}
    ).json()["id"]

    actual_priors = client.get(f"/experiments/{experiment_id}").json()["priors"]
    assert len(priors) == 10
    for name, prior in actual_priors.items():
        assert priors[name] == prior


def random_name() -> str:
    return f"xxx{uuid4()}"


def test_ensembles(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ids = {create_ensemble(experiment_id) for _ in range(5)}

    # Ensembles exist when using experiment list endpoint
    docs = client.get("/experiments").json()
    for doc in docs:  # Python doesn't have a built-in find function :(
        if doc["id"] == experiment_id:
            break
    else:
        raise KeyError(
            f"Experiment with id '{experiment_id}' not found in the list of experiments"
        )
    assert ids == set(doc["ensemble_ids"])

    # The list of ensembles belonging to the newly created experiment matches
    resp = client.get(f"/experiments/{experiment_id}/ensembles")
    assert ids == {ens["id"] for ens in resp.json()}


def test_ensemble_size(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")

    ensemble_size = random.randint(0, 1000)
    ensemble_id = create_ensemble(experiment_id=experiment_id, size=ensemble_size)

    resp = client.get(f"/ensembles/{ensemble_id}")
    assert ensemble_size == resp.json()["size"]


def test_delete_experiment(client, create_experiment, create_ensemble):
    num_experiments_before_test = len(client.get("/experiments").json())
    experiment_id = create_experiment("1")

    ensemble_id = create_ensemble(experiment_id, ["param1", "param2"])
    matrix = np.random.rand(5, 8, 13)

    # POST
    post_url = f"/ensembles/{ensemble_id}/records/mat/matrix"
    client.post(post_url, json=matrix.tolist())
    OBSERVATIONS = {
        "OBS1": {
            "values": [1, 2, 3],
            "errors": [0.1, 0.2, 0.3],
            "x_axis": ["0", "1", "2"],
        },
        "OBS2": {
            "values": [2, 4, 3],
            "errors": [0.9, 0.2, 0.3],
            "x_axis": ["2", "3", "4"],
        },
        "OBS3": {
            "values": [1, 4, 5],
            "errors": [0.1, 0.5, 0.2],
            "x_axis": ["5", "6", "7"],
        },
    }
    for name, obs in OBSERVATIONS.items():
        client.post(
            f"/experiments/{experiment_id}/observations",
            json=dict(
                name=name,
                values=obs["values"],
                errors=obs["errors"],
                x_axis=obs["x_axis"],
            ),
        )
    observations = client.get(f"/experiments/{experiment_id}/observations").json()
    client.delete(f"/experiments/{experiment_id}")
    assert len(client.get(f"/experiments").json()) == num_experiments_before_test
    for obs in observations:
        resp = client.get(f"/observations/{obs['id']}", check_status_code=None)
        assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_create_ensemble_with_overlap(client, create_experiment):
    experiment_id = create_experiment("test_ensembles")

    client.post(
        f"/experiments/{experiment_id}/ensembles",
        json={
            "size": 1,
            "parameter_names": ["foo", "bar", "coeff", "qux"],
            "response_names": ["coeff", "fopr", "fopt", "fgpt", "fgpr"],
        },
        check_status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
