import os
import sys
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


STORAGE_DATABASE_URL = "ERT_STORAGE_DATABASE_URL"


if STORAGE_DATABASE_URL not in os.environ:
    sys.exit(f"Environment variable '{STORAGE_DATABASE_URL}' not set")


IS_SQLITE = os.environ[STORAGE_DATABASE_URL].startswith("sqlite")
IS_POSTGRES = os.environ[STORAGE_DATABASE_URL].startswith("postgres")

if IS_SQLITE:
    engine = create_engine(
        os.environ[STORAGE_DATABASE_URL], connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(os.environ[STORAGE_DATABASE_URL])
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
