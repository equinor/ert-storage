import os
import pytest


@pytest.fixture
def azure_client():
    """
    A synchronous Azure Blob Storage ContainerClient
    """
    from ert_storage.database import HAS_AZURE_BLOB_STORAGE, ENV_BLOB, BLOB_CONTAINER

    if not HAS_AZURE_BLOB_STORAGE:
        pytest.skip("An Azure Storage connection is required to run these tests")

    import asyncio
    from ert_storage.database import create_container_if_not_exist
    from azure.storage.blob import ContainerClient

    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_container_if_not_exist())

    yield ContainerClient.from_connection_string(os.environ[ENV_BLOB], BLOB_CONTAINER)


def test_blob(client, azure_client):
    ensemble_id = _create_ensemble(client)

    # List all blobs prior to adding file
    pre_blobs = {blob.name for blob in azure_client.list_blobs()}

    # Standard file upload and download
    client.post_check(
        f"/ensembles/{ensemble_id}/records/foo/file",
        files={"file": ("somefile", open("/bin/bash", "rb"), "foo/bar")},
    )
    resp = client.get_check(f"/ensembles/{ensemble_id}/records/foo")
    assert resp.status_code == 200

    # List all blobs after adding file
    post_blobs = {blob.name for blob in azure_client.list_blobs()}

    diff_blobs = list(post_blobs - pre_blobs)
    assert len(diff_blobs) == 1

    blob = azure_client.get_blob_client(diff_blobs[0])
    assert blob.download_blob().readall() == resp.content


def _create_ensemble(client, parameters=[]):
    resp = client.post("/ensembles", json={"parameters": parameters})
    return resp.json()["id"]
