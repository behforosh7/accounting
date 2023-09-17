#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

gunicorn --bind 0.0.0.0:8000 app.wsgi &
python3 /app/radius.py 