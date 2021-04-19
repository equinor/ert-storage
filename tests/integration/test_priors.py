import pytest
from uuid import uuid4
from ert_storage import json_schema as js


def test_post_prior(client, make_prior):
    prior = make_prior()

    experiment_id = client.post(
        "/experiments", json={"name": "test", "priors": {"testpri": prior.dict()}}
    ).json()["id"]

    priors = client.get(f"/experiments/{experiment_id}/priors").json()
    assert len(priors) == 1
    assert priors["testpri"] == prior


def test_post_multiple_priors(client, make_random_priors):
    priors = {random_name(): prior for prior in make_random_priors(10)}

    experiment_id = client.post(
        "/experiments", data=js.ExperimentIn(name="footest", priors=priors).json()
    ).json()["id"]

    actual_priors = client.get(f"/experiments/{experiment_id}/priors").json()
    assert len(priors) == 10
    for name, prior in actual_priors.items():
        assert priors[name] == prior


def random_name() -> str:
    return f"xxx{uuid4()}"
