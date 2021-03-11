import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


class _TestClient(TestClient):
    def get_check(self, *args, **kwargs):
        resp = self.get(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError
        return resp

    def post_check(self, *args, **kwargs):
        resp = self.post(*args, **kwargs)
        if resp.status_code != 200:
            print(resp.text)
            raise AssertionError
        return resp


@pytest.fixture
def client():
    from ert_storage.app import app
    from ert_storage.database import get_db, engine, IS_SQLITE, IS_POSTGRES
    from ert_storage.database_schema import Base

    if IS_SQLITE:
        Base.metadata.create_all(bind=engine)

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
