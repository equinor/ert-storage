import time
import datetime

OBSERVATIONS = {
    "OBS1": {"values": [1, 2, 3], "errors": [0.1, 0.2, 0.3], "x_axis": ["0", "1", "2"]},
    "OBS2": {"values": [2, 4, 3], "errors": [0.9, 0.2, 0.3], "x_axis": ["2", "3", "4"]},
    "OBS3": {"values": [1, 4, 5], "errors": [0.1, 0.5, 0.2], "x_axis": ["5", "6", "7"]},
}

RECORDS = {
    "FOPR": [1.1, 2.1, 3.1],
    "WOPR": [1.2, 2.2, 3.2],
    "LOPR": [1.3, 2.3, 3.3],
    "COPR": [1.4, 2.4, 3.4],
    "MOPR": [1.5, 2.5, 3.5],
}


def test_observations(client, create_experiment):
    experiment_id = create_experiment("test_ensembles")
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

    uploaded_observations = client.get(
        f"/experiments/{experiment_id}/observations"
    ).json()
    for obs in uploaded_observations:
        assert obs["name"] in OBSERVATIONS
        assert obs["values"] == OBSERVATIONS[obs["name"]]["values"]
        assert obs["errors"] == OBSERVATIONS[obs["name"]]["errors"]
        assert obs["x_axis"] == OBSERVATIONS[obs["name"]]["x_axis"]


def test_observations_with_records(client, create_experiment, create_ensemble):
    experiment_id = create_experiment("test_ensembles")
    ensemble_id = create_ensemble(experiment_id=experiment_id)
    record_obs_association = {"OBS1": "FOPR", "OBS2": "LOPR", "OBS3": "LOPR"}

    for record, values in RECORDS.items():
        client.post(f"/ensembles/{ensemble_id}/records/{record}/matrix", json=values)
    ensemble_records = client.get(
        f"/ensembles/{ensemble_id}/records",
    ).json()

    for name, obs in OBSERVATIONS.items():
        record_name = record_obs_association[name]
        record = ensemble_records[record_name]
        client.post(
            f"/experiments/{experiment_id}/observations",
            json=dict(
                name=name,
                values=obs["values"],
                errors=obs["errors"],
                x_axis=obs["x_axis"],
                records=[record["id"]],
            ),
        )

    uploaded_observations = client.get(
        f"/experiments/{experiment_id}/observations"
    ).json()

    for obs in uploaded_observations:
        record_id = obs["records"][0]
        rec_obj = client.get(f"/records/{record_id}").json()
        assert record_obs_association[obs["name"]] == rec_obj["name"]
