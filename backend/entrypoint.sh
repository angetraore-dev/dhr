#!/bin/sh
# =====================================================================
# entrypoint.sh — Backend DHR
# Lance les migrations Alembic puis démarre uvicorn
# =====================================================================
set -e

echo "[entrypoint] Attente de la base de données..."
# Attente active que la DB réponde (le healthcheck Docker ne suffit pas
# toujours car le healthcheck peut être vert avant que les extensions
# soient prêtes)
python - <<'PY'
import sys, time
from sqlalchemy import create_engine, text
from app.config import get_settings

engine = create_engine(str(get_settings().database_url))
for i in range(60):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[entrypoint] DB prête.")
        sys.exit(0)
    except Exception as e:
        print(f"[entrypoint] DB pas prête ({i+1}/60) : {e}")
        time.sleep(2)
print("[entrypoint] Timeout attente DB.")
sys.exit(1)
PY

echo "[entrypoint] Application des migrations Alembic..."
alembic upgrade head

echo "[entrypoint] Démarrage uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload