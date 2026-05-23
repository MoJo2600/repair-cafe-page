#!/bin/sh
set -e

echo "==> Running database migrations..."
python /srv/app/run_migrations.py

echo "==> Starting services..."
exec supervisord -c /etc/supervisord.conf
