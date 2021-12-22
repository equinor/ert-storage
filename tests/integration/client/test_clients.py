import os
import json
import pytest
from fastapi import status
from ert_storage.client import _session
from ert_storage.client import Client, AsyncClient, ConnInfo


@pytest.mark.parametrize("explicit_conn_info", [False, True])
def test_client(start_server, explicit_conn_info):
    with start_server():
        conn_info = None
        if explicit_conn_info:
            assert _session._CACHED_CONN_INFO is None

            conn_info = ConnInfo.parse_raw(os.environ[_session.ENV_VAR])
            del os.environ[_session.ENV_VAR]

            # Check that the lack of explicit conn_info doesn't work now
            with pytest.raises(RuntimeError):
                with Client() as client:
                    client.get("/healthcheck")

        with Client(conn_info=conn_info) as client:
            resp = client.get("/healthcheck")
            assert resp.status_code == status.HTTP_200_OK

        with Client(conn_info=conn_info) as client:
            pre_exps = client.get("/experiments").json()

            assert client.post("/experiments", json={"name": "foo"}).status_code == 200

            post_exps = client.get("/experiments").json()
            assert len(pre_exps) + 1 == len(post_exps)

            # This assumes that experiments are ordered in insertion order
            assert post_exps[-1]["name"] == "foo"


@pytest.mark.parametrize("explicit_conn_info", [False, True])
@pytest.mark.asyncio
async def test_async_client(start_server, explicit_conn_info):
    with start_server():
        conn_info = None
        if explicit_conn_info:
            assert _session._CACHED_CONN_INFO is None

            conn_info = ConnInfo.parse_raw(os.environ[_session.ENV_VAR])
            del os.environ[_session.ENV_VAR]

            # Check that the lack of explicit conn_info doesn't work now
            with pytest.raises(RuntimeError):
                async with AsyncClient() as client:
                    await client.get("/healthcheck")

        async with AsyncClient(conn_info=conn_info) as client:
            resp = await client.get("/healthcheck")
            assert resp.status_code == status.HTTP_200_OK

        async with AsyncClient(conn_info=conn_info) as client:
            pre_exps = (await client.get("/experiments")).json()

            assert (
                await client.post("/experiments", json={"name": "bar"})
            ).status_code == 200

            post_exps = (await client.get("/experiments")).json()
            assert len(pre_exps) + 1 == len(post_exps)

            # This assumes that experiments are ordered in insertion order
            assert post_exps[-1]["name"] == "bar"
