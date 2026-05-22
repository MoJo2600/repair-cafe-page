# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /build

RUN corepack enable

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm build
# outDir in vite.config.ts is "../app/static/dist" relative to frontend/,
# so the build lands at /app/static/dist inside this stage.

# ── Stage 2: Python app ───────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System packages needed by some Python deps (e.g. PyMuPDF, Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 \
  && rm -rf /var/lib/apt/lists/*

# Python dependencies first (better layer caching)
COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ /app/
COPY wsgi.py ./
COPY config/ /config/

# Built frontend assets
COPY --from=frontend-builder /app/static/dist /app/static/dist

# Persistent data directory (mount a volume here in production)
RUN mkdir -p /data

EXPOSE 5000

# 1 worker + 4 threads: keeps APScheduler to a single process while still
# handling concurrent requests. Increase --threads on beefier hardware.
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", \
            "--workers", "1", \
            "--worker-class", "gthread", \
            "--threads", "4", \
            "--timeout", "120", \
            "wsgi:application"]