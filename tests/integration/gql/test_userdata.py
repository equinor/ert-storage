import json
import pytest


def post_experiment(client):
    item_id = client.post("/experiments", json={"name": "test_userdata"}).json()["id"]
    return (
        f"/experiments/{item_id}",
        f'{{ experiment(id: "{item_id}") {{ userdata }} }}',
        ["experiment"],
    )


def post_ensemble(client):
    exp_url, _, _ = post_experiment(client)
    item_id = client.post(
        f"{exp_url}/ensembles",
        json={"parameter_names": [], "response_names": [], "size": 0},
    ).json()["id"]
    return (
        f"/ensembles/{item_id}",
        f'{{ ensemble(id: "{item_id}") {{ userdata }} }}',
        ["ensemble"],
    )


@pytest.mark.parametrize("post_item", [post_experiment, post_ensemble])
def test_unset_userdata(client, post_item):
    _, item_query, item_json_path = post_item(client)

    # Execute query
    resp = client.gql_execute(item_query)

    # Navigate to userdata
    node = resp["data"]
    for key in item_json_path:
        node = node[key]
    actual_data = json.loads(node["userdata"])

    assert actual_data == {}


@pytest.mark.parametrize("post_item", [post_experiment, post_ensemble])
def test_userdata(client, post_item):
    item_url, item_query, item_json_path = post_item(client)

    # Set userdata
    data = {"test": "foo", "hello": {"world": 1}}
    client.put(f"{item_url}/userdata", json=data)

    # Execute query
    resp = client.gql_execute(item_query)

    # Navigate to userdata
    node = resp["data"]
    for key in item_json_path:
        node = node[key]
    actual_data = json.loads(node["userdata"])

    assert data == actual_data
