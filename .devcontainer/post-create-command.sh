#!/bin/bash
uv sync --locked --group dev
# uv run manage.py migrate
### If you prefer not to use django runserver
# uv run --group prod gunicorn --bind 0.0.0.0:8000 lidotiku.wsgi --reload
