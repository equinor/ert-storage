from setuptools import setup

with open("README.md") as f:
    long_description = f.read()


setup(
    name="ert-storage",
    description="Storage service for ERT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Equinor ASA",
    author_email="fg_sib-scout@equinor.com",
    url="https://github.com/equinor/ert-storage",
    license="GPLv3",
    packages=[
        "ert_storage",
        "ert_storage._alembic",
        "ert_storage._alembic.alembic",
        "ert_storage._alembic.alembic.versions",
        "ert_storage.database_schema",
        "ert_storage.endpoints",
        "ert_storage.endpoints.compute",
        "ert_storage.client",
        "ert_storage.compute",
        "ert_storage.ext",
        "ert_storage.json_schema",
        "ert_storage.testing",
    ],
    package_dir={
        "": "src",
    },
    package_data={
        "ert_storage": ["py.typed"],
        "ert_storage._alembic": ["alembic.ini"],
    },
    entry_points={
        "console_scripts": ["ert-storage=ert_storage.__main__:main"],
        "pytest11": ["ert-storage=ert_storage.testing.pytest11"],
    },
    extras_require={
        "test": [
            "black",
            "pytest",
            "pytest-asyncio",
            "mypy==0.981",
            "types-requests",
        ],
        "postgres": [
            "psycopg2",
        ],
        "azure": [
            "aiohttp",
            "azure-storage-blob",
        ],
    },
    install_requires=[
        "alembic",
        "fastapi < 0.100.0",
        "httpx",
        "numpy",
        "pandas",
        "pyarrow",
        "pydantic < 2",
        "python-multipart",
        "requests",
        "sqlalchemy>=1.4",
        "uvicorn >= 0.17.0",
    ],
)
