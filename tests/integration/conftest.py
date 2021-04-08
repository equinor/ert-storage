import pytest


@pytest.fixture
def client(ert_storage_client):
    """
    Simple rename of ert_storage_client -> client
    """
    return ert_storage_client


@pytest.fixture
def create_ensemble(client):
    def func(experiment_id, parameters=None, update_id=None):
        if parameters is None:
            parameters = []
        resp = client.post(
            f"/experiments/{experiment_id}/ensembles",
            json={"parameters": parameters, "update_id": update_id},
        )
        return str(resp.json()["id"])

    return func


@pytest.fixture
def create_experiment(client):
    def func(name):
        resp = client.post("/experiments", json={"name": name})
        return resp.json()["id"]

    return func


@pytest.fixture
def simple_ensemble(create_ensemble, create_experiment, request):
    def func(parameters=None, update_id=None):
        exp_id = create_experiment(request.node.name)
        ens_id = create_ensemble(exp_id, parameters=parameters, update_id=update_id)
        return ens_id

    return func
