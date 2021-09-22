import io
import numpy
from fastapi import status


def test_different_record_classes(client, simple_ensemble):
    ensemble_id = simple_ensemble()

    # Post matrix
    client.post(
        f"/ensembles/{ensemble_id}/records/foo/matrix",
        params={"realization_index": 0},
        json=[1, 2, 3],
    )

    # Post file under the same name should fail
    client.post(
        f"/ensembles/{ensemble_id}/records/foo/file",
        params={"realization_index": 1},
        files={"file": ("foo", io.BytesIO(b"foo"), "application/octet-stream")},
        check_status_code=status.HTTP_409_CONFLICT,
    )
