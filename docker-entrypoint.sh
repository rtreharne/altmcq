#!/bin/sh
set -e

mkdir -p "$(dirname "${SQLITE_PATH:-/data/db.sqlite3}")"
python manage.py migrate --noinput

exec "$@"
