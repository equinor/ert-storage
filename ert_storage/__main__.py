"""
Start a debug uvicorn server
"""
import os
import sys
import uvicorn
from typing import Optional
from tempfile import mkdtemp
from shutil import rmtree


def main() -> None:
    database_dir: Optional[str] = None
    if "ERT_STORAGE_DATABASE_URL" not in os.environ:
        print(
            "Environment variable 'ERT_STORAGE_DATABASE_URL' not set.\n"
            "Defaulting to development SQLite temporary database.\n"
            "Configure:\n"
            "1. File-based SQLite (development):\n"
            "\tERT_STORAGE_DATABASE_URL=sqlite:///ert.db\n"
            "2. PostgreSQL (production):\n"
            "\tERT_STORAGE_DATABASE_URL=postgresql:///<username>:<password>@<hostname>:<port>/<database>\n",
            file=sys.stderr,
        )
        database_dir = mkdtemp(prefix="ert-storage_")
        os.environ["ERT_STORAGE_DATABASE_URL"] = f"sqlite:///{database_dir}/ert.db"

    try:
        uvicorn.run(
            "ert_storage.app:app", reload=True, reload_dirs=[os.path.dirname(__file__)]
        )
    finally:
        if database_dir is not None:
            rmtree(database_dir)


if __name__ == "__main__":
    main()
