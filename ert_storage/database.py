import os
import sys
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


ENV_RDBMS = "ERT_STORAGE_DATABASE_URL"
ENV_BLOB = "ERT_STORAGE_AZURE_CONNECTION_STRING"
ENV_BLOB_CONTAINER = "ERT_STORAGE_AZURE_BLOB_CONTAINER"

if ENV_RDBMS not in os.environ:
    sys.exit(f"Environment variable '{ENV_RDBMS}' not set")


URI_RDBMS = os.environ[ENV_RDBMS]
IS_SQLITE = URI_RDBMS.startswith("sqlite")
IS_POSTGRES = URI_RDBMS.startswith("postgres")
HAS_AZURE_BLOB_STORAGE = ENV_BLOB in os.environ
BLOB_CONTAINER = os.getenv(ENV_BLOB_CONTAINER, "ert")


if IS_SQLITE:
    engine = create_engine(URI_RDBMS, connect_args={"check_same_thread": False})
else:
    engine = create_engine(URI_RDBMS)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


async def get_db() -> Any:
    db = Session()

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


if HAS_AZURE_BLOB_STORAGE:
    import asyncio
    from azure.core.exceptions import ResourceNotFoundError
    from azure.storage.blob.aio import ContainerClient

    azure_blob_container = ContainerClient.from_connection_string(
        os.environ[ENV_BLOB], BLOB_CONTAINER
    )

    async def create_container_if_not_exist() -> None:
        try:
            await azure_blob_container.get_container_properties()
        except ResourceNotFoundError:
            await azure_blob_container.create_container()
