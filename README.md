ERT Storage Server
====================================================

This is the permanent storage solution for the
[ERT](https://github.com/equinor/ert) project. It is written in Python 3.6+
using FastAPI, Pydantic, SQLAlchemy, Graphene and Azure Blob Storage.

# Development Environment

This section describes how to use ERT Storage for testing or development purposes. It uses an in-memory SQLite database with no Azure Blob Storage.

First, install ERT Storage into a Python virtual environment:

``` sh
# Clone this repo
git clone https://github.com/equinor/ert-storage
cd ert-storage

# Create the virtual environment (assuming you have Python 3.6+)
python3 -m venv my-venv

# Enable the environment
source my-venv/bin/activate       # sh/bash/zsh

# Install ERT Storage into the environment from current working directory
pip install -e .
```

Then start ERT Storage simply by using the new `ert-storage` command. This command will tell you that you are using an in-memory SQLite database. Now, using your browser, navigate to http://localhost:8000 to bring up the Swagger documentation page. Pages of note are:

- http://localhost:8000/doc Swagger
- http://localhost:8000/redoc ReDoc (alternative to Swagger)
- http://localhost:8000/gql Graph_i_QL, interactive GraphQL page

# Persisting data

Specifying the `ERT_STORAGE_DATABASE_URL` environment variable it is possible to
specify a non-in-memory database. Refer to [SQLAlchemy
Documentation](https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls)
for all possible database URLs. However, only SQLite and PostgreSQL with default
SQLAlchemy drivers are officially supported at this time.

## SQLite
To persist a SQLite database (note the number of forward slashes `/`):

``` sh
export ERT_STORAGE_DATABASE_URL="sqlite:///ert.db"       # Use ert.db in current working directory
export ERT_STORAGE_DATABASE_URL="sqlite:////tmp/ert.db"  # Use /tmp/ert.db
```

NOTE: SQLite does not support the same features as PostgreSQL, and as such
migrations (via `alembic`) are not supported and some data may be stored or
fetched in an inefficient manner. You will have to delete your data whenever we
update the database schema, which happens relatively often.

## PostgreSQL
We use PostgreSQL in production and we use `alembic` for migrations. The following will set everything up.


Set `ERT_STORAGE_DATABASE_URL`
``` sh
# Example postgres settings
HOST="localhost"
PORT=5432  # default PostgreSQL port
DATA="ert_store"
USER="my-usrnam"
PASS="my-passwd"

# The connection string is then:
export ERT_STORAGE_DATABASE_URL="postgresql://${USER}:${PASS}@${HOST}:${PORT}/${DATA}"

# or
export ERT_STORAGE_DATABASE_URL="postgresql://my-usrnam:my-passwd@localhost:5432/ert_store"
```

Then install a compatible SQLAlchemy PostgreSQL driver, such as
[`psycopg2`](https://pypi.org/project/psycopg2/). We provide the extras
requirement `postgres` which installs the necessary requirements.

``` sh
pip install -e .[postgres]
```

The `psycopg2` package requires the postgres client development headers to be
installed on your machine. The
[`psycopg2-binary`](https://pypi.org/project/psycopg2-binary/) is a precompiled
version of this package that might be compatible with your OS and PostgreSQL
version.

### Database setup: Container
You can use either Docker or `podman` to easily start a postgres instance as a
container. On modern Linux distributions it is easier to use the `podman`
project.

[See the docker.io page for postgres for more information](https://hub.docker.com/_/postgres/)

The following instructions are for `podman`. Replacing `podman` with `docker` will 

``` sh
# Start the container in the background, with password 'password', forwarding the port 5432 to the host.
podman run --name ert-storage-pg -e POSTGRES_PASSWORD=password -p 5432:5432 -d docker.io/postgres

# Useful commands
podman stop ert-storage-pg
podman start ert-storage-pg
podman kill ert-storage-pg  # SIGTERM
podman rm ert-storage-pg    # Remove the container entirely

# Use with ERT Storage
export ERT_STORAGE_DATABASE_URL="postgresql://postgres:password@localhost:5432/postgres"

```

To reset the database, do:
``` sh
podman exec ert-storage-pg sh -c "dropdb -U postgres postgres; createdb -U postgres postgres"
ert-storage alembic upgrade head
```

### Database setup: Linux service

First, install the dependencies:

``` sh
# RHEL / CentOS / Fedora
sudo yum install postgresql-server postgresql-devel

# Ubuntu
sudo apt install postgresql postgresql-client
```

Then, initialize the database and configure a user with a password.

``` sh
# Initialise stuff in /var (OPTIONAL)
sudo -i -u postgres -- initdb

# Create superuser
sudo -i -u postgres -- createuser -s ert_user

# Give yourself a password (default is to disallow password login)
sudo -i -u postgres -- psql -c "alter user ert_user with password '12345';"

# Create a database with you as its owner
createdb -U ert_user ert_db

# Set the database URL so that ERT Storage can connect to it
# You will need to redo this every time you close your shell
export ERT_STORAGE_DATABASE_URL="postgresql://ert_user:12345@localhost:5432/ert_db"
```

To recreate the database, do:

``` sh
dropdb ert_db && createdb -O ert_user ert_db
ert-storage alembic upgrade head
```

### After setup
Once a PostgreSQL server is running, you need to apply alembic migrations.
`ert-storage` provides a wrapper around the `alembic` command which
automatically selects the correct alembic configuration.

``` sh
# Upgrade to latest migration
ert-storage alembic upgrade head
```

# Azure Blob Storage
ERT Storage supports Azure Blob Storage for storing opaque data. This feature is invisible to the user. Install the `azure` extras with `pip install ert-storage[azure]`.

Set the `ERT_STORAGE_AZURE_CONNECTION_STRING` environment variable to the connection string found in
your Azure configuration to have ERT Storage use Azure Blob Storage.

## Local instance for development
It is possible to use [Azurite](https://github.com/Azure/Azurite), an open source Azure Storage implementation, for testing and development purposes.

As a container:
``` sh
# Podman
podman run --name ert-storage-az -p 10000:10000 -p 10001:10001 -d mcr.microsoft.com/azure-storage/azurite

# Let ERT Storage know about Azurite
export ERT_STORAGE_AZURE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
```

# Development
For development, install the `test` extras `pip install ert-storage[test]`,
which installs `black`, `pytest` and `mypy`. Run tests using `pytest`.

All integration tests must be able to pass when using a non-empty production
database. In practice that means that each test needs to create a unique
"experiment".

During test debugging it might be helpful to have the tests persist data in the
database. The following environment variable tells ERT Storage not to rollback the data after each test.

``` sh
export ERT_STORAGE_NO_ROLLBACK=1
```
