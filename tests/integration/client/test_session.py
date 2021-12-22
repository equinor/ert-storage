import os
import pytest
from ert_storage.client import _session

INVALID_CONFIGS = ["{}", "not a json", '{"auth_token": "x"}']
VALID_CONFIGS = {
    '{"base_url": "http://localhost"}': _session.ConnInfo(base_url="http://localhost"),
    '{"base_url": "http+unix:///tmp/sock", "auth_token": "x"}': _session.ConnInfo(
        base_url="http+unix:///tmp/sock", auth_token="x"
    ),
}


def test_missing_configuration(monkeypatch):
    monkeypatch.setenv("ERT_STORAGE_CONNECTION_STRING", "")
    with pytest.raises(RuntimeError):
        _session.find_conn_info()


@pytest.mark.parametrize("config", INVALID_CONFIGS)
def test_invalid_configuration_env(monkeypatch, config):
    monkeypatch.setenv("ERT_STORAGE_CONNECTION_STRING", config)
    with pytest.raises(RuntimeError):
        _session.find_conn_info()


@pytest.mark.parametrize("config", VALID_CONFIGS.items())
def test_valid_configuration_env(monkeypatch, config):
    monkeypatch.setenv("ERT_STORAGE_CONNECTION_STRING", config[0])
    assert _session.find_conn_info() == config[1]


@pytest.mark.parametrize("config", INVALID_CONFIGS)
def test_invalid_configuration_file(monkeypatch, tmp_path, config):
    config_file = tmp_path / "storage_server.json"
    config_file.write_text(config)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError):
        _session.find_conn_info()


@pytest.mark.parametrize("config", VALID_CONFIGS.items())
def test_valid_configuration_file(monkeypatch, tmp_path, config):
    config_file = tmp_path / "storage_server.json"
    config_file.write_text(config[0])
    monkeypatch.chdir(tmp_path)
    assert _session.find_conn_info() == config[1]


@pytest.mark.parametrize("config", INVALID_CONFIGS)
def test_invalid_configuration_file_recursive(monkeypatch, tmp_path, config):
    config_file = tmp_path / "storage_server.json"
    config_file.write_text(config)

    working_dir = tmp_path / "a" / "b" / "c"
    working_dir.mkdir(parents=True)

    monkeypatch.chdir(working_dir)
    with pytest.raises(RuntimeError):
        _session.find_conn_info()


@pytest.mark.parametrize("config", VALID_CONFIGS.items())
def test_valid_configuration_file_recursive(monkeypatch, tmp_path, config):
    config_file = tmp_path / "storage_server.json"
    config_file.write_text(config[0])

    working_dir = tmp_path / "a" / "b" / "c"
    working_dir.mkdir(parents=True)

    monkeypatch.chdir(working_dir)
    assert _session.find_conn_info() == config[1]


def test_cache():
    conn_info = _session.ConnInfo(base_url="http://1.2.3.4", auth_token="y")
    os.environ["ERT_STORAGE_CONNECTION_STRING"] = conn_info.json()

    assert _session.find_conn_info() == conn_info

    del os.environ["ERT_STORAGE_CONNECTION_STRING"]
    assert _session.find_conn_info() == conn_info
