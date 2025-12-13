#!/bin/sh
set -e

mkdir -p /app/storage/database \
         /app/storage/cache \
         /app/storage/cover \
         /app/storage/logs \
         /app/storage/avatars

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4