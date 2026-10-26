# =====================================================================
# backend/Dockerfile — FastAPI + Python 3.12
# =====================================================================
FROM python:3.12-slim AS base

# --- Métadonnées ---
LABEL maintainer="DHR" \
      description="Back-end FastAPI pour la centralisation des ouvrages hydrauliques ruraux"

# --- Variables d'environnement Python ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3

# --- Dépendances système ---
# - build-essential + libpq-dev : compilation psycopg / psycopg2
# - libgeos-dev, libproj-dev, gdal-bin, libgdal-dev : requis par GeoAlchemy2 / Shapely
# - curl : utile pour le healthcheck (fallback)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Répertoire de travail ---
WORKDIR /app

# --- Installation des dépendances Python ---
# On copie d'abord pyproject.toml pour profiter du cache Docker
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install -e .

# --- Copie du code applicatif ---
COPY app ./app

# --- Dossier pour les fichiers uploadés ---
RUN mkdir -p /app/uploads && chmod 755 /app/uploads

# --- Utilisateur non-root (sécurité) ---
RUN useradd --create-home --shell /bin/bash dhr \
    && chown -R dhr:dhr /app
USER dhr

# --- Port exposé ---
EXPOSE 8000

# --- Point d'entrée ---
# --reload en dev : hot-reload quand le code change (volume monté)
# --host 0.0.0.0 : accessible depuis l'extérieur du container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]