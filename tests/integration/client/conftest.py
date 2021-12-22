import os
import re
import sys
import pytest
import subprocess
from contextlib import contextmanager
from ert_storage.client import _session


@pytest.fixture(autouse=True)
def disable_cache(monkeypatch):
    monkeypatch.setattr(_session, "_CACHED_CONN_INFO", None)


@pytest.fixture()
def start_server(monkeypatch, tmp_path, request):
    @contextmanager
    def func():
        server_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "--no-use-colors",
                "--port=0",
                "ert_storage.app:app",
            ],
            env={
                **os.environ,
                "ERT_STORAGE_DATABASE_URL": f"sqlite:///{tmp_path / 'ert.db'}",
            },
            stdout=sys.stdout,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        while server_proc.poll() is None:
            assert server_proc.stderr is not None
            line = server_proc.stderr.readline().decode()
            print(line, file=sys.stderr, end="")
            # This is very dependent on uvicorn continuing to print this log message
            # in future versions. If tests that depend on this fixture don't start,
            # it might be that the text has been changed.
            match = re.search(
                r"Uvicorn running on ([a-z0-9.:/]+) \(Press CTRL\+C to quit\)", line
            )
            if match:
                base_url = match[1]
                break

        # Set connection information
        conn_info = _session.ConnInfo(base_url=base_url, auth_token="hunter2")
        monkeypatch.setenv(_session.ENV_VAR, conn_info.json())

        assert server_proc.poll() is None
        request.addfinalizer(lambda: server_proc.terminate())
        yield server_proc

    return func
