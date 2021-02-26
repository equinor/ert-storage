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
    },
    install_requires=[
        "async-exit-stack; python_version < '3.7'",
        "async-generator; python_version < '3.7'",
        "alembic",
        "fastapi",
        "psycopg2",
        "python-multipart",
        "requests",
        "sqlalchemy",
    ],
)
