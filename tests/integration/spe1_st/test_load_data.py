import pytest


@pytest.mark.spe1
def test_read_experiments(requests_get):
    experiments = requests_get("experiments").json()
    assert len(experiments) == 1


@pytest.mark.spe1
def test_read_priors(get_experiment_dict):
    exp = get_experiment_dict
    prior = {"function": "uniform", "min": 0.1, "max": 0.9}
    # test for parameter's priors
    assert "FIELD_PROPERTIES:POROSITY" in exp["priors"]
    assert prior == exp["priors"]["FIELD_PROPERTIES:POROSITY"]

    assert "FIELD_PROPERTIES:X_MID_PERMEABILITY" in exp["priors"]
    assert prior == exp["priors"]["FIELD_PROPERTIES:X_MID_PERMEABILITY"]


@pytest.mark.spe1
def test_read_parameters(requests_get, get_ensemble_id):
    ens_id = get_ensemble_id

    # get list of parameter names
    parameters = requests_get(f"ensembles/{ens_id}/parameters").json()

    # test for parameters
    assert {"FIELD_PROPERTIES:POROSITY", "FIELD_PROPERTIES:X_MID_PERMEABILITY"} == set(
        parameters
    )

    # test for parameter shape
    param1 = requests_get(f"ensembles/{ens_id}/records/{parameters[0]}").json()
    param2 = requests_get(f"ensembles/{ens_id}/records/{parameters[1]}").json()

    assert len(param1) == 2
    assert len(param2) == 2


@pytest.mark.spe1
def test_read_observations(requests_get, get_ensemble_id):
    ens_id = get_ensemble_id

    # test for observations
    obs = requests_get(f"ensembles/{ens_id}/observations").json()
    assert len(obs) == 1
    assert obs[0]["name"] == "WOPT:PROD"
    assert obs[0]["errors"] == [1e6, 1e6, 1e6]
    assert obs[0]["values"] == [1e7, 2e7, 3e7]
    assert len(obs[0]["records"]) == 2

    # test that the record has observations
    obs1 = requests_get(
        f"ensembles/{ens_id}/records/{obs[0]['name']}/observations",
        params={"realization_index": 0},
    ).json()

    obs2 = requests_get(
        f"ensembles/{ens_id}/records/{obs[0]['name']}/observations",
        params={"realization_index": 1},
    ).json()

    assert obs == obs1
    assert obs == obs2


@pytest.mark.spe1
def test_read_responses(requests_get, get_ensemble_id):
    ens_id = get_ensemble_id

    # test for responses
    resp = requests_get(f"ensembles/{ens_id}/responses").json()

    assert {"WGPT:PROD", "WWPT:PROD", "WOPT:PROD", "WWIT:INJ"} == resp.keys()

    # test for reponse data shape
    for response in resp.keys():
        response_real_0 = requests_get(
            f"ensembles/{ens_id}/records/{response}",
            params={"realization_index": 0},
        ).json()
        response_real_1 = requests_get(
            f"ensembles/{ens_id}/records/{response}",
            params={"realization_index": 1},
        ).json()

        # test the data size
        assert len(response_real_0) == 108
        assert len(response_real_1) == 108
