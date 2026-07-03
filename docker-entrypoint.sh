#!/usr/bin/env bash
# Start the baked-in PostgreSQL cluster, then run the Flask API in the same
# container. Postgres listens on all container interfaces so that publishing
# port 5432 (docker run -p 5432:5432) lets you develop against the assignment
# data from your host; password auth (user/password: assignment) is required
# for non-local connections.
set -euo pipefail

: "${PGDATA:=/opt/pgdata}"

echo "Starting PostgreSQL..."
gosu postgres pg_ctl -D "$PGDATA" -o "-c listen_addresses='*'" -w start

echo "Starting API on port 8000..."
exec gunicorn --bind 0.0.0.0:8000 run:app
