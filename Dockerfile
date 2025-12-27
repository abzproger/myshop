# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System dependencies (psycopg2, Pillow, etc.)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30 -o Acquire::ForceIPv4=true \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Poetry for dependency management
ARG POETRY_VERSION=2.0.1
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -U pip setuptools wheel \
    && python -m pip install "poetry==${POETRY_VERSION}"

# Install Python dependencies first (better layer caching)
COPY pyproject.toml poetry.lock /app/
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-ansi --only main

# Project sources
COPY . /app



