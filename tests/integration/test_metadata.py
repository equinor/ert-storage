import pytest


def post_ensemble(client):
    # generate an ensemble
    resp = client.post("/experiments", json={"name": "test_metadata"})
    exp_id = resp.json()["id"]
    resp = client.post(f"/experiments/{exp_id}/ensembles", json={"parameters": []})
    ens_id = resp.json()["id"]
    return f"/ensembles/{ens_id}"


def post_experiment(client):
    # generate an ensemble
    resp = client.post("/experiments", json={"name": "test_metadata"})
    exp_id = resp.json()["id"]
    return f"/experiments/{exp_id}"


def post_record(client, name="rec_test", data="[1, 2, 3, 4, 5]"):
    # generate a record
    ens_url = post_ensemble(client)
    rec_url = f"{ens_url}/records/{name}"
    client.post(
        f"{rec_url}/matrix",
        data=data,
    )
    return rec_url


def post_observation(client):
    # generate an observation
    resp = client.post("/experiments", json={"name": "test_metadata"})
    exp_id = resp.json()["id"]
    _url = f"/experiments/{exp_id}/observations"
    resp = client.post(
        f"/experiments/{exp_id}/observations",
        json=dict(
            name="OBS1",
            values=[1, 2, 3],
            errors=[0.1, 0.2, 0.3],
            x_axis=["0", "1", "2"],
        ),
    )
    obs_id = resp.json()["id"]
    return f"/observations/{obs_id}"


@pytest.mark.parametrize(
    "base", [post_record, post_ensemble, post_experiment, post_observation]
)
def test_metadata(client, base):
    _url = base(client)
    metadata_in = dict(msg_user="Reference model")
    client.put(f"{_url}/metadata", json=metadata_in)
    metadata_out = client.get(f"{_url}/metadata").json()
    assert metadata_in == metadata_out

    metadata_in_update = dict(msg_system=dict(error="NO_ERROR"))
    client.patch(f"{_url}/metadata", json=metadata_in_update)

    metadata_out = client.get(f"{_url}/metadata").json()
    metadata_in.update(metadata_in_update)
    assert metadata_out == metadata_in
