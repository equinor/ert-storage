import os
import pytest
from ert_storage.testing import testclient


HTTP_VERBS = ("get", "post", "put", "patch", "delete")


class MockResponse:
    @property
    def status_code(self):
        return 404

    @property
    def content(self):
        return b""


class MockHTTPClient:
    def __getattribute__(self, name):
        return self.request if name in HTTP_VERBS else super().__getattribute__(name)

    def request(self, *args, **kwargs):
        return MockResponse()


class TestClient(testclient._TestClient):
    def __init__(self):
        self.http_client = MockHTTPClient()


@pytest.mark.parametrize("should_raise", [False, True])
def test_rest(should_raise):
    tc = TestClient()
    tc.raise_on_client_error = should_raise

    for verb in HTTP_VERBS:
        http_func = getattr(tc, verb)

        if should_raise:
            with pytest.raises(testclient.ClientError, match="Status code was 404"):
                http_func("/testpath")
        else:
            assert http_func("/testpath").status_code == 404


def test_environ(monkeypatch):
    monkeypatch.delenv("ERT_STORAGE_DATABASE_URL", raising=False)
    pre_env = os.environ.copy()

    with testclient.testclient_factory():
        pass

    assert pre_env == os.environ
