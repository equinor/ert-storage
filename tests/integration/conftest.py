import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


class _TestClient(TestClient):
    def get_check(self, *args, **kwargs):
        resp = self.get(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError(f"Status code was {resp.status_code}, expected 200")
        return resp

    def post_check(self, *args, **kwargs):
        resp = self.post(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError(f"Status code was {resp.status_code}, expected 200")
        return resp

    def put_check(self, *args, **kwargs):
        resp = self.put(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError(f"Status code was {resp.status_code}, expected 200")
        return resp

    def patch_check(self, *args, **kwargs):
        resp = self.patch(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError(f"Status code was {resp.status_code}, expected 200")
        return resp


@pytest.fixture
def client():
    from ert_storage.app import app
    from ert_storage.database import (
        get_db,
        engine,
        IS_SQLITE,
        IS_POSTGRES,
        HAS_AZURE_BLOB_STORAGE,
    )
    from ert_storage.database_schema import Base

    if IS_SQLITE:
        Base.metadata.create_all(bind=engine)
    if HAS_AZURE_BLOB_STORAGE:
        import asyncio
        from ert_storage.database import create_container_if_not_exist

        loop = asyncio.get_event_loop()
        loop.run_until_complete(create_container_if_not_exist())

    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=connection)

    async def override_get_db():
        db = TestSession()

        # Make PostgreSQL return float8 columns with highest precision. If we don't
        # do this, we may lose up to 3 of the least significant digits.
        if IS_POSTGRES:
            db.execute("SET extra_float_digits=3")
        try:
            yield db
            db.commit()
            db.close()
        except:
            db.rollback()
            db.close()
            raise

    app.dependency_overrides[get_db] = override_get_db
    yield _TestClient(app)

    # teardown: rollback database to before the test.
    # For debugging change rollback to commit.
    transaction.rollback()
    connection.close()


@pytest.fixture
def create_ensemble(client):
    def func(experiment_id, parameters=None):
        if parameters is None:
            parameters = []
        resp = client.post_check(
            f"/experiments/{experiment_id}/ensembles", json={"parameters": parameters}
        )
        return resp.json()["id"]

    return func


@pytest.fixture
def create_experiment(client):
    def func(name):
        resp = client.post_check("/experiments", json={"name": name})
        return resp.json()["id"]

    return func


@pytest.fixture
def simple_ensemble(create_ensemble, create_experiment, request):
    def func(parameters=None):
        exp_id = create_experiment(request.node.name)
        ens_id = create_ensemble(exp_id, parameters=parameters)
        return ens_id

    return func
