import pytest


def test_add_labels_successfully(client, simple_ensemble):
    # generate an ensemble
    ensemble_id = simple_ensemble()
    client.post(f"/ensembles/{ensemble_id}/records/hello/matrix", data="[1,2,3,4]")
    labels_in = [[0, 1, 2, 3], ["colA"]]
    client.post(f"/ensembles/{ensemble_id}/records/hello/labels", json=labels_in)

    labels_out = client.get(f"/ensembles/{ensemble_id}/records/hello/labels")
    print(labels_out)
