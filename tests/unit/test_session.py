import pytest
import os
from ert_storage.client.session import Session

INVALID_CONFIG = "{}"
VALID_CONFIG = """
{"urls": ["http://127.0.0.1:51842","http://fubar:51842","http://snafu:51842"],
"authtoken": "STyksdnjsdn "
}"""


def test_missing_configuration(monkeypatch):
    monkeypatch.setenv("ERT_STORAGE_CONNECTION_STRING", "")
    with pytest.raises(RuntimeError):
        with Session():
            pass


def test_invalid_configuration_env(monkeypatch):
    monkeypatch.setenv("ERT_STORAGE_CONNECTION_STRING", INVALID_CONFIG)
    with pytest.raises(RuntimeError):
        with Session():
            pass


def test_invalid_configuration_file(tmp_path):
    config_file = tmp_path / "storage_server.json"
    config_file.write_text(INVALID_CONFIG)
    os.chdir(tmp_path)
    with pytest.raises(RuntimeError):
        with Session():
            pass


def test_no_server_configuration_env(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "*")
    monkeypatch.setenv("ERT_STORAGE_CONNECTION_STRING", VALID_CONFIG)
    with pytest.raises(RuntimeError):
        with Session():
            pass


def test_no_server_configuration_file(monkeypatch, tmp_path):
    monkeypatch.setenv("NO_PROXY", "*")
    config_file = tmp_path / "storage_server.json"
    config_file.write_text(VALID_CONFIG)
    os.chdir(tmp_path)
    with pytest.raises(RuntimeError):
        with Session():
            pass
