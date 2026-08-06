#!/bin/bash
# Install dependencies
uv sync --locked --group dev

# Run Django migrations
# uv run manage.py migrate

# Run the Django development server
# uv run --group dev python manage.py runserver
# If you prefer not to use Django development server, you can use Gunicorn instead:
# uv run --group prod gunicorn --bind 0.0.0.0:8000 lidotiku.wsgi --reload
