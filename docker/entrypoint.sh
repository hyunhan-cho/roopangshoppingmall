#!/bin/sh
set -e

echo "[entrypoint] Starting web container..."

# If DATABASE_URL is postgres, wait for DB to be ready
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -qi '^postgres'; then
  echo "[entrypoint] Waiting for Postgres..."
  ATTEMPTS=0
  MAX_ATTEMPTS=60
  SLEEP_SEC=2
  python - <<'PY' || true
import os, sys, time
import psycopg
from urllib.parse import urlparse

url = os.getenv('DATABASE_URL')
if not url:
    sys.exit(0)

attempts = 0
max_attempts = int(os.getenv('DB_MAX_ATTEMPTS', '60'))
sleep_sec = float(os.getenv('DB_SLEEP_SEC', '2'))
while attempts < max_attempts:
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                print('[entrypoint] Postgres is ready')
                sys.exit(0)
    except Exception as e:
        attempts += 1
        print(f"[entrypoint] Waiting for Postgres... ({attempts}/{max_attempts})", flush=True)
        time.sleep(sleep_sec)

print('[entrypoint] Postgres not ready in time', file=sys.stderr)
sys.exit(1)
PY
fi

# Migrations
echo "[entrypoint] Running database migrations"
python manage.py migrate --noinput

# Collect static files (also done at build time, but safe to re-run)
echo "[entrypoint] Collecting static files"
python manage.py collectstatic --noinput || true

echo "[entrypoint] Starting Gunicorn"
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout 120


