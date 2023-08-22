#!/bin/bash

set -e

gunicorn --bind 0.0.0.0:8080 lidotiku.wsgi