#!/bin/sh
set -e

echo "Running Alembic database migrations..."
alembic upgrade head

echo "Starting Uvicorn FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
