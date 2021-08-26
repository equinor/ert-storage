import os
import pytest


def test_help_missing_env_rdbms(monkeypatch):
    # A user reported to us that invoking python -c "help('modules')" failed with
    # "Environment variable 'ERT_STORAGE_DATABASE_URL' not set" in the cli.
    # This test is to verify that replacing 'sys.exit' ( if 'ENV_RDBMS' is
    # missing from 'os.environ' ) with i.e 'EnvironmentError' it can be treated with
    # a normal try / except clause ( which seems like how it is handled in the 'help'
    # function )

    monkeypatch.delenv("ERT_STORAGE_DATABASE_URL", raising=False)

    with pytest.raises(Exception) as e:
        from ert_storage import database

        database.get_env_rdbms()

    assert str(e.value) == "Environment variable 'ERT_STORAGE_DATABASE_URL' not set"


def test_help_with_env_rdbms(monkeypatch):
    db_url = "sqlite:///foo.bar"
    monkeypatch.setenv("ERT_STORAGE_DATABASE_URL", db_url)

    from ert_storage import database

    act_rdbms = database.get_env_rdbms()

    assert db_url == act_rdbms
