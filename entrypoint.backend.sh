#!/bin/sh
set -e

echo "==> Running database migrations..."
python /srv/app/run_migrations.py

echo "==> Starting Gunicorn..."
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 1 \
  --worker-class gthread \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  wsgi:application
