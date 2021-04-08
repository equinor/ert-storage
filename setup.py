from setuptools import setup


setup(
    name="ert-storage",
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
        "ert_storage.ext",
        "ert_storage.graphql",
        "ert_storage.json_schema",
    ],
    package_data={
        "ert_storage._alembic": [
            "alembic.ini",
        ]
    },
    entry_points={
        "console_scripts": ["ert-storage=ert_storage.__main__:main"],
        "pytest11": ["ert-storage=ert_storage.testing.pytest11"],
    },
    extras_require={
        "test": [
            "black",
            "pytest",
            "mypy",
        ],
        "postgres": [
            "psycopg2",
        ],
    },
    install_requires=[
        "aiohttp",
        "alembic",
        "async-exit-stack; python_version < '3.7'",
        "async-generator; python_version < '3.7'",
        "azure-storage-blob",
        "fastapi",
        "graphene",
        "graphene-sqlalchemy>=2.0",
        "numpy",
        "pydantic",
        "python-multipart",
        "requests",
        "sqlalchemy>=1.4",
        "starlette==0.13.6",
        "uvicorn",
    ],
)
