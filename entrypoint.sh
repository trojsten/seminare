#!/bin/bash
set -euo pipefail

python manage.py wait_for_database

type="${1:-prod}"

if [ "$type" = "dev" ]; then
  uv run pygmentize -S monokai -f html -a .codehilite >/app/seminare/style/static/code.css

  python manage.py migrate
  exec python manage.py runserver 0.0.0.0:8000 --force-color
else
  python manage.py migrate
  exec /base/gunicorn.sh seminare.wsgi
fi
