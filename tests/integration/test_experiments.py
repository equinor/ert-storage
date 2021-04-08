def test_list(client, create_experiment):

    expected_experiments = {"test1", "test2", "test3"}
    for name in expected_experiments:
        create_experiment(name)

    docs = [
        exp
        for exp in client.get_check("/experiments").json()
        if exp["name"] in expected_experiments
    ]

    assert expected_experiments == {exp["name"] for exp in docs}
    assert all(exp["ensembles"] == [] for exp in docs)


def test_ensembles(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ids = {create_ensemble(experiment_id) for _ in range(5)}

    # Ensembles exist when using experiment list endpoint
    docs = client.get_check("/experiments").json()
    for doc in docs:  # Python doesn't have a built-in find function :(
        if doc["id"] == experiment_id:
            break
    else:
        raise KeyError(
            f"Experiment with id '{experiment_id}' not found in the list of experiments"
        )
    assert ids == set(doc["ensembles"])

    # The list of ensembles belonging to the newly created experiment matches
    resp = client.get_check(f"/experiments/{experiment_id}/ensembles")
    assert ids == {ens["id"] for ens in resp.json()}
