import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def default_database():
    if "ERT_STORAGE_DATABASE_URL" not in os.environ:
        os.environ["ERT_STORAGE_DATABASE_URL"] = "sqlite:///:memory:"
        print("Using in-memory SQLite database for tests")
