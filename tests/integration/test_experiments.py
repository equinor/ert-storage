import numpy as np
from fastapi import status


def test_list(client, create_experiment):

    expected_experiments = {"test1", "test2", "test3"}
    for name in expected_experiments:
        create_experiment(name)

    docs = [
        exp
        for exp in client.get("/experiments").json()
        if exp["name"] in expected_experiments
    ]

    assert expected_experiments == {exp["name"] for exp in docs}
    assert all(exp["ensembles"] == [] for exp in docs)


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
    assert ids == set(doc["ensembles"])

    # The list of ensembles belonging to the newly created experiment matches
    resp = client.get(f"/experiments/{experiment_id}/ensembles")
    assert ids == {ens["id"] for ens in resp.json()}


def test_delete_experiment(client, create_experiment, create_ensemble):
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
    assert len(client.get(f"/experiments").json()) == 0
    for obs in observations:
        resp = client.get(f"/observations/{obs['id']}", check_status_code=None)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
