ERT Storage Postgresql edition (tm) proof-of-concept
====================================================

# Setup
These instructions are for RHEL 7.

## Setup PostgreSQL
Install the required packages. On RHEL 7 these are for postgres 9, which is probably ok.

``` sh
sudo yum install postgresql-server postgresql-devel
```

Then, initialize the database and configure a user with a password.

``` sh
# Initialise stuff in /var
sudo su -i -l postgres -- initdb

# Create superuser
sudo su -i -l postgres -- createuser -s pg_ert

# Give yourself a password (default is to disallow password login)
sudo su -i -l postgres -- psql -c "alter user pg_ert with password = '12345'\;"

# Create a database with you as its owner
createdb -U pg_ert db_ert

# Set the database URL so that ERT Storage can connect to it
# You will need to redo this every time you close your shell
export ERT_STORAGE_DATABASE_URL="postgresql://pg_ert:12345@localhost:5432/db_ert"
```

## Setup ERT Storage
Install this project in a virtualenv. Among other things, this will pull and
compile `psycopg2`, which is the PostgreSQL driver (hence the requirement for
`postgresql-devel`).

``` sh
pip install -e .[test]
```

Then, using Alembic, update the database schema.
``` sh
alembic upgrade head
```

And you should be done setting up!

# Using

Start ERT Storage using Uvicorn. `--reload` means that Uvicorn will detect
changes in any files that you edit and automatically reload the application.

``` sh
uvicorn ert_storage.app:app --reload
```

Navigate to https://localhost:8000/docs to see the Swagger docs

To create migrations, use:

``` sh
alembic revision --autogenerate --message="[Describe your changes]"
# Inspect and maybe edit the generated file
alembic upgrade head
```

Sometimes you'll need to drop and recreate the database:

``` sh
dropdb -U pg_ert db_ert
createdb -U pg_ert db_ert
alembic upgrade head
```
