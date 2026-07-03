#!/usr/bin/env bash
# Load the assignment data into your own PostgreSQL instance for local
# development (an alternative to publishing the container's port 5432).
#
# Usage: DATABASE_URL_PSQL="postgresql://assignment:assignment@localhost:5432/recsys" \
#            scripts/load_local_db.sh
#
# The target database and user must already exist, e.g.:
#   createuser assignment --pwprompt
#   createdb recsys --owner assignment
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_URL="${DATABASE_URL_PSQL:-postgresql://assignment:assignment@localhost:5432/recsys}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

gunzip -kc "$REPO_ROOT/db/items.csv.gz" > "$WORKDIR/items.csv"
gunzip -kc "$REPO_ROOT/db/interactions.csv.gz" > "$WORKDIR/interactions.csv"

psql "$DB_URL" -v ON_ERROR_STOP=1 \
    -f "$REPO_ROOT/db/init_db.sql" \
    -c "\copy items (item_id,title,subtitle,author,description,categories,store,price,main_category) FROM '$WORKDIR/items.csv' WITH (FORMAT csv, HEADER true)" \
    -c "\copy interactions (user_id,item_id,timestamp) FROM '$WORKDIR/interactions.csv' WITH (FORMAT csv, HEADER true)"

psql "$DB_URL" -t -c "select 'Loaded ' || (select count(*) from items) || ' items, ' || (select count(*) from interactions) || ' interactions.'"
