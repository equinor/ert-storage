import os
from typing import Any
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from ert_storage.security import security

ENV_BLOB = "ERT_STORAGE_AZURE_CONNECTION_STRING"
ENV_RDBMS = "ERT_STORAGE_DATABASE_URL"
ENV_BLOB_CONTAINER = "ERT_STORAGE_AZURE_BLOB_CONTAINER"


class ErtStorageConfig:
    def __init__(self):
        self._engine = None
        self._session = None
        self._uri_rdbms = None

    def get_uri_rdbms(self) -> str:
        if self._uri_rdbms is None:
            if ENV_RDBMS not in os.environ:
                raise EnvironmentError(f"Environment variable '{ENV_RDBMS}' not set")
            self._uri_rdbms = os.environ[ENV_RDBMS]

        return self._uri_rdbms

    def is_sqlite(self) -> str:
        uri_rdbms = self.get_uri_rdbms()
        return uri_rdbms.startswith("sqlite")

    def is_postgres(self) -> str:
        uri_rdbms = self.get_uri_rdbms()
        return uri_rdbms.startswith("postgres")

    @staticmethod
    def has_azure_blob_storage() -> str:
        return ENV_BLOB in os.environ

    @staticmethod
    def blob_container() -> str:
        return os.getenv(ENV_BLOB_CONTAINER, "ert")

    def get_engine(self) -> Engine:
        if self._engine is None:
            uri_rdbms = self.get_uri_rdbms()
            if self.is_sqlite():
                self._engine = create_engine(
                    uri_rdbms, connect_args={"check_same_thread": False}
                )
            else:
                self._engine = create_engine(uri_rdbms, pool_size=50, max_overflow=100)
        return self._engine

    def get_session(self) -> Session:
        if self._session is None:
            self._session = sessionmaker(
                autocommit=False, autoflush=False, bind=self.get_engine()
            )

        return self._session()


ert_storage_config = ErtStorageConfig()
Base = declarative_base()


async def get_db(*, _: None = Depends(security)) -> Any:
    db = ert_storage_config.get_session()

    # Make PostgreSQL return float8 columns with highest precision. If we don't
    # do this, we may lose up to 3 of the least significant digits.
    if ert_storage_config.is_postgres():
        db.execute("SET extra_float_digits=3")
    try:
        yield db
        db.commit()
        db.close()
    except:
        db.rollback()
        db.close()
        raise


if ert_storage_config.has_azure_blob_storage():
    import asyncio
    from azure.core.exceptions import ResourceNotFoundError
    from azure.storage.blob.aio import ContainerClient

    azure_blob_container = ContainerClient.from_connection_string(
        os.environ[ENV_BLOB], ert_storage_config.blob_container()
    )

    async def create_container_if_not_exist() -> None:
        try:
            await azure_blob_container.get_container_properties()
        except ResourceNotFoundError:
            await azure_blob_container.create_container()
