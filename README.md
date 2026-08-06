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

- JSON: `ENV=local uv run manage.py generateschema --file openapi-schema.json --format openapi-json --generator_class api.schemas.LidoSchemaGenerator`
- YAML: `ENV=local uv run manage.py generateschema --file openapi-schema.yml --generator_class api.schemas.LidoSchemaGenerator`

To view the docs in swagger-ui you can use `/swagger` to access. Optionally you can load it to some other swagger-ui with the url for `/openapi-schema.json`

# Local development

## Running the API locally

Utilize Django runserver:

`ENV=local uv run manage.py runserver`

or with Gunicorn:

`ENV=local uv run --group prod gunicorn --bind 0.0.0.0:8000 lidotiku.wsgi --reload`

## Devcontainer

The project is set up with devcontainer, which will allow running a containerized development environment with VSCode. You will need the extension `ms-vscode-remote.remote-containers`, and also `docker` and `docker-compose`.

Before opening the project in the devcontainer, copy the local environment template and adjust values as needed:

```
cp .devcontainer/.env.local.example .devcontainer/.env.local
```

`.devcontainer/.env.local` is git-ignored, so it is safe to put personal/local secrets there. It is read automatically when running commands with `ENV=local` (see e.g. [Testing](#testing) and [Typing](#typing)).

Once the project is opened in a devcontainer, the environment should be set for development. It should be possible to run it remotely also for example with GitHub Codespaces.

The devcontainer installs the development dependencies with `uv sync --locked --group dev` and installs Ruff separately with `uv tool`. VS Code uses the project `.venv` and the Ruff extension for Python formatting and lint fixes.

Two containers are run, one for the Django application and one for the PostgreSQL database with the PostGIS extension.

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
`ENV=local uv run mypy . --check-untyped-defs`

This is to be automated later in the build process.

## Testing

The project is configured with pytest (pytest-django).
Use a database that has been configured with `db_init.sql` and `lido_test_backup.sql`

To run the tests:

`ENV=local uv run pytest`

To find which lines don't have test coverage:

`ENV=local uv run pytest --cov-config=.coveragerc --cov=api/ --cov-report term-missing`

## Updating requirements

[uv](https://docs.astral.sh/uv/) is used to manage dependencies. Production dependencies are
listed in `[project.dependencies]`, development dependencies in
`[dependency-groups.dev]`, and production-only extras (e.g. `uwsgi`) in
`[dependency-groups.prod]` in `pyproject.toml`.

To add or update a dependency, run e.g.:

```
uv add some-package
uv add --group dev some-dev-package
```

To sync your local environment with the lockfile:

```
uv sync --locked
```

## Code format

This project uses [Ruff](https://docs.astral.sh/ruff/) for code formatting and quality checking.

Ruff is installed separately with `uv tool`, run automatically via the
`pre-commit` hooks, and configured as the VS Code formatter and linter in the
devcontainer. Run the standalone `ruff` command directly.

Basic `ruff` commands:

* lint: `ruff check`
* apply safe lint fixes: `ruff check --fix`
* check formatting: `ruff format --check`
* format: `ruff format`

[`pre-commit`](https://pre-commit.com/) can be used to install and
run all the formatting tools as git hooks automatically before a
commit.

## Commit message format

New commit messages must adhere to the [Conventional Commits](https://www.conventionalcommits.org/)
specification, and line length is limited to 72 characters.

When [`pre-commit`](https://pre-commit.com/) is in use, [
`commitlint`](https://github.com/conventional-changelog/commitlint)
checks new commit messages for the correct format.

## Availability checks

The availability of the API can be checked via the `/readiness` and `/healthz` endpoints.
