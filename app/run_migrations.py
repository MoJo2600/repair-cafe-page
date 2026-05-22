#!/usr/bin/env python
"""
Run database migrations. Does not require a running Flask application —
the database URL is built from environment variables (MYSQL_HOST, MYSQL_DATABASE,
MYSQL_USER, MYSQL_PASSWORD, MYSQL_PORT).
"""

import os
import sys

# Put the project root on sys.path so 'app' can be imported by env.py
app_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(app_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from alembic import command
from alembic.config import Config

migrations_dir = os.path.join(app_dir, "migrations")
alembic_cfg = Config(os.path.join(migrations_dir, "alembic.ini"))
alembic_cfg.set_main_option("script_location", migrations_dir)

print("Running database migrations...")
command.upgrade(alembic_cfg, "head")
print("Migrations completed successfully!")
