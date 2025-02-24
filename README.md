# LIDO-TIKU API

REST API for the City of Helsinki traffic observation data.
Data is collected from multiple sources and different types of sensors that measure different types of traffic, for example counts on passing cars from certain directions or their average speed. The measurements can be of e.g. vehicles, pedestrians and bicycles.

# Database

**The database is not managed by Django!** Do not attempt to make writes to the default tables, nor change their schema.

The data in the database is accessed with views. First create these views, Django will not do that as it is not managing the database. The create commands can be found in `.devcontainer/db_init.sql`.
Ensure that the database user has access to these views, if there are issues on that end.
For instance:

```sql
GRANT SELECT ON TABLE lido.vw_counters TO database_user;
GRANT SELECT ON TABLE lido.vw_observations TO database_user;
```

# API documentation

OpenAPIv3 spec documentation is generated dynamically.

To access it you can view `/openapi-schema.json`.

Static file can also be generated:

- JSON: `ENV=local ./manage.py generateschema --file openapi-schema.json --format openapi-json --generator_class api.schemas.LidoSchemaGenerator`
- YAML: `ENV=local ./manage.py generateschema --file openapi-schema.yml --generator_class api.schemas.LidoSchemaGenerator`

To view the docs in swagger-ui you can use `/swagger` to access. Optionally you can load it to some other swagger-ui with the url for `/openapi-schema.json`

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

The database can be populated with a full dump from the LIDO database, or the locally available `lido_test_backup.sql` which contains a limited sample from the full database.
It is recommended to use the sample if running tests for performance reasons.

1. Initialize the database schema, tables, indexes, views etc.:

`psql --dbname=postgres --username=postgres --host=localhost --port=5431 < .devcontainer/db_init.sql`

2. Take a dump from the database (replace host in the following script):

`pg_dump --data-only --dbname=lido_liikennelaskenta --schema=lido --username=lido_api --host=0.0.0.0 > lido_backup_$(date +'%Y-%m-%dT%H:%M').sql`

3. Restore the data (only):

`psql --dbname=postgres --username=postgres --host=localhost --port=5431 < /tmp/pgdump/lido_backup_2023-08-01T13\:41.sql`

2.  OR use the sample:
    `psql --dbname=postgres --username=postgres --host=localhost --port=5431 < .devcontainer/lido_test_backup.sql`

## Typing

To check typing run:
`ENV=local mypy . --check-untyped-defs`

This is to be automated later in the build process.

## Testing

The project is configured with pytest (pytest-django).
Use a database that has been configured with `db_init.sql` and `lido_test_backup.sql`

To run the tests:

`ENV=local pytest`

To find which lines don't have test coverage:

`ENV=local pytest --cov-config=.coveragerc --cov=api/ --cov-report term-missing`

## Availability checks

The availability of the API can be checked via the `/readiness` and `/healthz` endpoints.
