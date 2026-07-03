# Single self-contained image: PostgreSQL 15 + the Flask API in one container.
# The assignment database (schema + data) is baked into the image at build time,
FROM postgres:15

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    ARTIFACT_DIR=/app/artifacts \
    PATH="/opt/venv/bin:$PATH"

# Python runtime on top of the Postgres (Debian) base image.
# libsuitesparse-dev provides the CHOLMOD headers needed to build scikit-sparse
# (a dependency of the `sansa` package).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-dev build-essential libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m venv /opt/venv
COPY requirements.txt ./
# Install the CPU build of torch first: the container has no GPU and the
# default CUDA wheels would add several GB to the image.
RUN pip install --no-cache-dir "torch>=2.2,<3.0" --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY run.py ./
RUN mkdir -p /app/artifacts

# --- Bake the assignment database into the image ----------------------------
# Use a PGDATA path OUTSIDE the base image's declared VOLUME
# (/var/lib/postgresql/data) so the initialized cluster and data persist in the
# image layer instead of being discarded.
ENV PGDATA=/opt/pgdata
COPY db/init_db.sql db/items.csv.gz db/interactions.csv.gz /assignment-db/

RUN set -eux; \
    mkdir -p "$PGDATA"; \
    gunzip -f /assignment-db/items.csv.gz /assignment-db/interactions.csv.gz; \
    chown -R postgres:postgres "$PGDATA" /assignment-db; \
    gosu postgres initdb -D "$PGDATA"; \
    gosu postgres pg_ctl -D "$PGDATA" -o "-c listen_addresses='localhost'" -w start; \
    gosu postgres psql -v ON_ERROR_STOP=1 --username postgres \
        -c "CREATE USER assignment WITH PASSWORD 'assignment';" \
        -c "CREATE DATABASE recsys OWNER assignment;"; \
    gosu postgres psql -v ON_ERROR_STOP=1 -h 127.0.0.1 --username assignment --dbname recsys -f /assignment-db/init_db.sql; \
    gosu postgres psql -v ON_ERROR_STOP=1 -h 127.0.0.1 --username assignment --dbname recsys \
        -c "\copy items (item_id,title,subtitle,author,description,categories,store,price,main_category) FROM '/assignment-db/items.csv' WITH (FORMAT csv, HEADER true)" \
        -c "\copy interactions (user_id,item_id,timestamp) FROM '/assignment-db/interactions.csv' WITH (FORMAT csv, HEADER true)"; \
    gosu postgres pg_ctl -D "$PGDATA" -m fast -w stop; \
    echo "host all all 0.0.0.0/0 scram-sha-256" >> "$PGDATA/pg_hba.conf"

COPY docker-entrypoint.sh /usr/local/bin/assignment-entrypoint.sh
RUN chmod +x /usr/local/bin/assignment-entrypoint.sh

# 8000 = API. 5432 = the bundled PostgreSQL - publish it with -p 5432:5432 to
# develop against the assignment data from your host (see README).
EXPOSE 8000 5432

ENTRYPOINT ["/usr/local/bin/assignment-entrypoint.sh"]
