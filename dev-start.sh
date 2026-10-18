#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ $# -gt 1 || (${1:-} != "" && ${1:-} != "--database-only" && ${1:-} != "--setup") ]]; then
    echo "Usage: bash dev-start.sh [--database-only|--setup]" >&2
    exit 1
fi

for dependency in docker python; do
    if ! command -v "$dependency" >/dev/null; then
        echo "Required command not found: $dependency" >&2
        exit 1
    fi
done

CONTAINER_PROJECT="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' "${HOSTNAME:-}" 2>/dev/null || true)"
if [[ "$CONTAINER_PROJECT" == "<no value>" ]]; then
    CONTAINER_PROJECT=""
fi
COMPOSE_PROJECT="${DEV_COMPOSE_PROJECT:-${CONTAINER_PROJECT:-$(basename "$ROOT_DIR")_devcontainer}}"
export MYSQL_HOST="${MYSQL_HOST:-${CONTAINER_PROJECT:+db}}"
export MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
export MYSQL_DATABASE="${MYSQL_DATABASE:-repaircafepage_dev}"
export MYSQL_USER="${MYSQL_USER:-root}"
export MYSQL_PASSWORD="${MYSQL_PASSWORD:-mariadb}"
export FLASK_ENV=development
export FLASK_SECRET_KEY="${FLASK_SECRET_KEY:-repaircafe-local-development-only}"

echo "Starting development database (Compose project: $COMPOSE_PROJECT)..."
DATABASE_ID="$(docker ps -aq --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" --filter 'label=com.docker.compose.service=db')"
if [[ -n "$DATABASE_ID" ]]; then
    docker start "$DATABASE_ID" >/dev/null
else
    docker compose --project-name "$COMPOSE_PROJECT" -f "$ROOT_DIR/.devcontainer/docker-compose.yml" up -d db
    DATABASE_ID="$(docker compose --project-name "$COMPOSE_PROJECT" -f "$ROOT_DIR/.devcontainer/docker-compose.yml" ps -q db)"
fi

echo "Waiting for MariaDB to accept connections..."
DATABASE_DEADLINE=$((SECONDS + 120))
until docker exec "$DATABASE_ID" healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1; do
    if (( SECONDS >= DATABASE_DEADLINE )); then
        echo "MariaDB did not become ready within 120 seconds. Check: docker logs $DATABASE_ID" >&2
        exit 1
    fi
    sleep 1
done

if [[ ! "$MYSQL_DATABASE" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "Development database names must contain only letters, numbers, and underscores." >&2
    exit 1
fi
echo "Ensuring development database exists: $MYSQL_DATABASE"
docker exec -e "DEV_DATABASE=$MYSQL_DATABASE" "$DATABASE_ID" sh -c \
    'exec mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`$DEV_DATABASE\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"'

if [[ ${1:-} == "--database-only" ]]; then
    echo "Development database is ready."
    exit 0
fi

if ! python "$ROOT_DIR/app/run_migrations.py"; then
    echo "Database migrations failed; development servers were not started." >&2
    echo "Use a database compatible with this checkout. Do not reset migration history to bypass errors." >&2
    exit 1
fi

if [[ ${1:-} == "--setup" ]]; then
    python "$ROOT_DIR/app/seed_dev.py"
    echo "Development database migrated and seeded: $MYSQL_DATABASE"
    exit 0
fi

for dependency in pnpm setsid; do
    if ! command -v "$dependency" >/dev/null; then
        echo "Required command not found: $dependency" >&2
        exit 1
    fi
done

if [[ ! -d frontend/node_modules ]]; then
    pnpm --dir "$ROOT_DIR/frontend" install --frozen-lockfile
fi

SERVER_PIDS=()
cleanup() {
    trap - EXIT INT TERM
    echo "Stopping development servers (database is left running)..."
    for server_pid in "${SERVER_PIDS[@]}"; do
        kill -TERM -- "-$server_pid" 2>/dev/null || true
    done
    wait || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "$ROOT_DIR/app"
setsid python -m flask --app run.py --debug run --host 0.0.0.0 --port 5000 &
SERVER_PIDS+=("$!")

cd "$ROOT_DIR/frontend"
setsid pnpm dev --port 5173 --strictPort &
SERVER_PIDS+=("$!")

echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:5000"
echo "Press Ctrl+C to stop both servers. Database data is preserved."

set +e
wait -n "${SERVER_PIDS[@]}"
SERVER_STATUS=$?
set -e
if [[ $SERVER_STATUS -eq 0 ]]; then
    echo "A development server stopped unexpectedly." >&2
    SERVER_STATUS=1
fi
exit "$SERVER_STATUS"
