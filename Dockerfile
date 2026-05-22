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

# ── Stage 2: Python app + Nginx ──────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# nginx for static-file serving; supervisor to manage both processes
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 \
    nginx \
    supervisor \
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

# Nginx + supervisor config
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisord.conf
# Remove the default nginx site so only our config is active
RUN rm -f /etc/nginx/sites-enabled/default

# Persistent data directory (mount a volume here in production)
RUN mkdir -p /data

# nginx runs on 80; Gunicorn is internal-only (127.0.0.1:5000)
EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisord.conf"]