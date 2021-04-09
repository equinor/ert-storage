import ert_storage.json_schema as js


def _create_dummy_update_id(algorithm, ensemble_id, client, transformations=[]):
    update_resp = client.post_check(
        f"/updates",
        json=dict(
            ensemble_reference_id=ensemble_id,
            algorithm=algorithm,
            observation_transformations=transformations,
        ),
    )
    return js.UpdateOut.parse_obj(update_resp.json()).id


def _get_ensemble(client, ensemble_id) -> js.EnsembleOut:
    resp = client.get_check(f"ensembles/{ensemble_id}")
    return js.EnsembleOut.parse_obj(resp.json())


def test_ensemble_parent_child_link(client, simple_ensemble):
    ensemble_0_id = simple_ensemble()

    update_ens1_id = _create_dummy_update_id("bogosort", ensemble_0_id, client)
    ensemble_1_id = simple_ensemble(update_id=update_ens1_id)

    update_ens2_id = _create_dummy_update_id("dijkstra", ensemble_0_id, client)
    ensemble_2_id = simple_ensemble(update_id=update_ens2_id)

    ens_0 = _get_ensemble(client, ensemble_0_id)
    ens_1 = _get_ensemble(client, ensemble_1_id)
    ens_2 = _get_ensemble(client, ensemble_2_id)

    assert ens_0.parent is None
    assert ens_1.parent == ens_0.id
    assert ens_2.parent == ens_0.id
    assert set(ens_0.children) == {ensemble_1_id, ensemble_2_id}


OBSERVATIONS = {
    "OBS1": {"values": [1, 2, 3], "errors": [0.1, 0.2, 0.3], "x_axis": ["0", "1", "2"]},
    "OBS2": {"values": [2, 4, 3], "errors": [0.9, 0.2, 0.3], "x_axis": ["2", "3", "4"]},
    "OBS3": {"values": [1, 4, 5], "errors": [0.1, 0.5, 0.2], "x_axis": ["5", "6", "7"]},
}
TRANSFORMATIONS = {
    "OBS1": {"scale": [0.5, 0.1, 1], "active": [True, True, False]},
    "OBS2": {"scale": [0.5, 1, 0.1], "active": [True, False, True]},
    "OBS3": {"scale": [1, 0.1, 2], "active": [False, True, True]},
}


def test_observation_transformations(client, create_ensemble, create_experiment):
    experiment_id = create_experiment("dummy")
    ensemble_parent = create_ensemble(experiment_id)
    for name, obs in OBSERVATIONS.items():
        client.post_check(
            f"/experiments/{experiment_id}/observations",
            json=dict(
                name=name,
                values=obs["values"],
                errors=obs["errors"],
                x_axis=obs["x_axis"],
            ),
        )

    uploaded_observations = client.get_check(
        f"/experiments/{experiment_id}/observations"
    ).json()
    mapping = {obs["name"]: obs["id"] for obs in uploaded_observations}
    transformations = [
        dict(
            name=name,
            observation_id=mapping[name],
            scale=trans["scale"],
            active=trans["active"],
        )
        for name, trans in TRANSFORMATIONS.items()
    ]
    update_id = _create_dummy_update_id(
        "bogosort", ensemble_parent, client, transformations=transformations
    )
    ensemble_child = create_ensemble(experiment_id, update_id=update_id)
    used_observations = client.get_check(
        f"/ensembles/{ensemble_child}/observations"
    ).json()
    for obs_json in used_observations:
        obs = js.ObservationOut.parse_obj(obs_json)
        assert obs.transformation.scale == TRANSFORMATIONS[obs.name]["scale"]
        assert obs.transformation.active == TRANSFORMATIONS[obs.name]["active"]
