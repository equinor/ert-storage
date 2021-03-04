import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def default_database(tmp_path_factory):
    if "ERT_STORAGE_DATABASE_URL" not in os.environ:
        path = tmp_path_factory.mktemp("database")
        os.environ["ERT_STORAGE_DATABASE_URL"] = f"sqlite:///{path / 'ert.db'}"
        print("Using temporary SQLite database for tests")
