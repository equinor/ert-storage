from setuptools import setup


setup(
    name="ert-storage",
    version="0.1.0",
    description="Storage service for ERT",
    author="Equinor ASA",
    author_email="fg_sib-scout@equinor.com",
    url="https://github.com/equinor/ert-storage",
    license="GPLv3",
    packages=["ert_storage", "ert_storage.endpoints"],
    extras_require={
        "python_version < '3.7": [
            "async-exit-stack",
            "async-generator",
        ],
        "test": [
            "black",
            "pytest",
            "mypy",
            "uvicorn",
        ],
    },
    install_requires=[
        "alembic",
        "fastapi",
        "psycopg2",
        "python-multipart",
        "sqlalchemy",
    ],
)
