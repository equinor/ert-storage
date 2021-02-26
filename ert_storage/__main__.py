"""
Start a debug uvicorn server
"""
import os
import sys


def main() -> None:
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "ert_storage.app:app",
            "--reload",
            "--reload-dir",
            os.path.dirname(__file__),
        ],
    )


if __name__ == "__main__":
    main()
