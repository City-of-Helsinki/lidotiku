# LIDO-TIKU API

# Local development

## Running the API locally

Utilize django runserver:

`./manage.py runserver`

or e.g. gunicorn:

`gunicorn --bind 0.0.0.0:8000 lidotiku.wsgi --reload`

## Devcontainer

The project is set up with devcontainer, which will allow running a containerized development environment with VSCode. You will need the extension `ms-vscode-remote.remote-containers`, and also `docker` and `docker-compose`.

Once the project is opened in a devcontainer, the environment should be set for development. It should be possible to run it remotely also for example with GitHub Codespaces.

Two containers are run, one for the django application and one for the PostgreSQL database with the PostGIS extension.

## Database

**This project does not manage the database schema!** Therefore do not try to make changes to the schema using Django migrations, nor do not add, update, or delete data from the database.

LIDO-TIKU utilizes PostgreSQL with **PostGIS** extension, it will be needed.

### Importing data to a local PostgreSQL

Prerequisites: You need the psql tooling `psql` and `pg_dump`. Get them one way or another, or run these commands inside the database container. E.g. for debian based distributions: `apt install postgresql-client`

1. Initialize the database schema, tables, indexes, views etc.:

`psql --dbname=postgres --username=postgres --host=localhost < .devcontainers/db_init.sql`


2. Take a dump from the database (replace host in the following script):

`pg_dump --data-only --dbname=lido_liikennelaskenta --schema=lido --username=lido_api --host=0.0.0.0 > lido_backup_$(date +'%Y-%m-%dT%H:%M').sql`

3. Restore the data (only):

`psql --dbname=postgres --username=postgres --host=localhost < /tmp/pgdump/lido_backup_2023-08-01T13\:41.sql`
