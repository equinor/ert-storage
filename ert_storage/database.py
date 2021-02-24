import os
import sys
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


STORAGE_DATABASE_URL = "ERT_STORAGE_DATABASE_URL"


if STORAGE_DATABASE_URL not in os.environ:
    sys.exit(f"{STORAGE_DATABASE_URL}")


engine = create_engine(os.environ[STORAGE_DATABASE_URL])
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


async def get_db() -> Any:
    db = Session()
    try:
        yield db
    finally:
        db.close()
