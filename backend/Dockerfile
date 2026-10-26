FROM python:3.12-slim AS base

LABEL maintainer="DHR"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY entrypoint.sh ./

RUN mkdir -p /app/uploads && chmod 755 /app/uploads
RUN chmod +x /app/entrypoint.sh

RUN useradd --create-home --shell /bin/bash dhr \
    && chown -R dhr:dhr /app
USER dhr

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]