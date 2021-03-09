from setuptools import setup


setup(
    name="ert-storage",
    version="0.1.0",
    description="Storage service for ERT",
    author="Equinor ASA",
    author_email="fg_sib-scout@equinor.com",
    url="https://github.com/equinor/ert-storage",
    license="GPLv3",
    packages=[
        "ert_storage",
        "ert_storage._alembic",
        "ert_storage._alembic.alembic",
        "ert_storage._alembic.alembic.versions",
        "ert_storage.endpoints",
    ],
    package_data={
        "ert_storage._alembic": [
            "alembic.ini",
        ]
    },
    entry_points={
        "console_scripts": ["ert-storage=ert_storage.__main__:main"],
    },
    extras_require={
        "test": [
            "black",
            "pytest",
            "mypy",
            "uvicorn",
        ],
        "postgres": [
            "psycopg2",
        ],
    },
    install_requires=[
        "alembic",
        "async-exit-stack; python_version < '3.7'",
        "async-generator; python_version < '3.7'",
        "fastapi",
        "numpy",
        "pydantic",
        "python-multipart",
        "requests",
        "sqlalchemy",
    ],
)
