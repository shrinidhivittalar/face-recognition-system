#!/bin/sh
# Container entrypoint for hosted deployment (Render).
#
# Exists so the platform's start command contains no shell metacharacters.
# Passing `a && b` directly proved fragile: the platform re-wraps the command,
# and the inner shell treated the whole string as one command name:
#   sh: 1: python scripts/init_db.py && uvicorn ...: not found
#
# create_all is idempotent, so running it on every boot is safe.
set -e

echo "Initializing database schema..."
python scripts/init_db.py

echo "Starting API on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --app-dir backend
