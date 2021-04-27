import pytest


@pytest.fixture
def client(ert_storage_client):
    """
    Simple rename of ert_storage_client -> client
    """
    return ert_storage_client


@pytest.fixture
def create_ensemble(client):
    def func(experiment_id, parameters=None, update_id=None, size=-1):
        if parameters is None:
            parameters = []
        resp = client.post(
            f"/experiments/{experiment_id}/ensembles",
            json={"parameters": parameters, "update_id": update_id, "size": size},
        )
        return str(resp.json()["id"])

    return func


@pytest.fixture
def create_experiment(client):
    def func(name, priors={}):
        resp = client.post("/experiments", json={"name": name, "priors": priors})
        return resp.json()["id"]

    return func


@pytest.fixture
def simple_ensemble(create_ensemble, create_experiment, request):
    def func(parameters=None, update_id=None, size=-1):
        exp_id = create_experiment(request.node.name)
        ens_id = create_ensemble(
            exp_id, parameters=parameters, update_id=update_id, size=size
        )
        return ens_id

    return func


from random import random, choices
from ert_storage.json_schema import prior


def make_const_prior() -> prior.PriorConst:
    return prior.PriorConst(value=random())


def make_trig_prior() -> prior.PriorTrig:
    return prior.PriorTrig(min=random(), max=random(), mode=random())


def make_normal_prior() -> prior.PriorNormal:
    return prior.PriorNormal(mean=random(), std=random())


def make_lognormal_prior() -> prior.PriorLogNormal:
    return prior.PriorLogNormal(mean=random(), std=random())


def make_truncnormal_prior() -> prior.PriorErtTruncNormal:
    return prior.PriorErtTruncNormal(
        mean=random(), std=random(), min=random(), max=random()
    )


def make_stdnormal_prior() -> prior.PriorStdNormal:
    return prior.PriorStdNormal()


def make_uniform_prior() -> prior.PriorUniform:
    return prior.PriorUniform(min=random(), max=random())


def make_duniform_prior() -> prior.PriorErtDUniform:
    return prior.PriorErtDUniform(bins=random(), min=random(), max=random())


def make_loguniform_prior() -> prior.PriorLogUniform:
    return prior.PriorLogUniform(min=random(), max=random())


def make_erf_prior() -> prior.PriorErtErf:
    return prior.PriorErtErf(
        min=random(), max=random(), skewness=random(), width=random()
    )


def make_derf_prior() -> prior.PriorErtDErf:
    return prior.PriorErtDErf(
        bins=random(), min=random(), max=random(), skewness=random(), width=random()
    )


MAKE_PRIOR = [
    make_const_prior,
    make_trig_prior,
    make_normal_prior,
    make_lognormal_prior,
    make_truncnormal_prior,
    make_stdnormal_prior,
    make_uniform_prior,
    make_duniform_prior,
    make_loguniform_prior,
    make_erf_prior,
    make_derf_prior,
]


@pytest.fixture
def make_random_priors():
    def maker(count):
        return [fn() for fn in choices(MAKE_PRIOR, k=count)]

    return maker


def pytest_generate_tests(metafunc):
    """
    Parameterise prior mocking functions without requiring us to import MAKE_PRIOR
    """

    if "make_prior" in metafunc.fixturenames:
        metafunc.parametrize("make_prior", MAKE_PRIOR)
