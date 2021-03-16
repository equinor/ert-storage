def test_list(client, create_experiment):

    expected_experiments = {"test1", "test2", "test3"}
    for name in expected_experiments:
        create_experiment(name)

    resp = client.get_check(f"/experiments")
    assert expected_experiments == {exp["name"] for exp in resp.json()}


def test_ensembles(client, create_experiment, create_ensemble):
    nr_of_ensembles = 5
    experiment_id = create_experiment("test_ensembles")
    ids = {create_ensemble(experiment_id) for i in range(nr_of_ensembles)}
    resp = client.get_check(f"/experiments/{experiment_id}/ensembles")
    assert ids == {ens["id"] for ens in resp.json()}
