import os
import sys
from subprocess import run, PIPE


def test_formatting():
    proc = run(
        [
            sys.executable,
            "-m",
            "black",
            "--check",
            os.path.join(os.path.dirname(__file__), ".."),
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if proc.returncode != 0:
        raise AssertionError(f"Black exited with code {proc.returncode}")


def test_typing():
    proc = run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--package=ert_storage",
            "--ignore-missing-imports",
            "--disallow-untyped-defs",
            "--show-error-codes",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if proc.returncode != 0:
        raise AssertionError(f"Mypy exited with code {proc.returncode}")
