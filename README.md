# RepairCafePage

Web application for managing repair café events — intake, repair logging,
electrical safety testing (VDE), and customer signatures.
Designed for self-hosted deployment on a Raspberry Pi or any Linux server.

## Features

- **Repair intake** — register devices with customer contact, device type,
  and defect description; capture liability signature on-screen or via QR code
- **Work log** — multiple repairer sessions per repair, each with duration and notes
- **VDE electrical safety testing** — record DIN VDE 0701/0702 test results
  and download a filled Prüfprotokoll PDF
- **Status tracking** — Offen → In Arbeit → Repariert / Nicht reparierbar
- **User management** — admin and repairer accounts with session-based auth
- **Settings** — configurable dropdown values (repair types, test devices)
  managed through the UI
- **Data export** — XLSX export; optional e-mail delivery

## Quick start (Docker)

Requirements: Docker + Docker Compose v2.

```bash
git clone https://github.com/MoJo2600/repaircafepage.git
cd repaircafepage

# Copy and edit environment variables
cp .env.example .env
$EDITOR .env

# Build and start — database migrations run automatically on first boot
docker compose up -d
```

The app is available at `http://<host>`.

### Update

```bash
docker compose pull
docker compose up -d
# Migrations run automatically on backend startup — no manual step needed.
```

### Stack overview

The stack runs as three containers:

| Container | Role | Exposed port |
|---|---|---|
| `frontend` | nginx — serves the Vue SPA, proxies `/api/` to the backend | 80 |
| `backend` | Gunicorn/Flask — API + PDF/email services | internal only |
| `db` | MariaDB 11 | internal only |

Multi-arch images (`linux/amd64` + `linux/arm64`) are published to GHCR so the
same `docker compose up -d` works on a Raspberry Pi 4/5 without changes.

### Persistent data

| Volume | Contents |
|---|---|
| `db_data` | MariaDB database |
| `app_data` | PDFs, log attachments, runtime data (`/data`) |

```bash
# Database dump
docker compose exec db mariadb-dump -u root -p"$MYSQL_ROOT_PASSWORD" repaircafepage > backup.sql

# App data backup
docker run --rm -v repaircafepage_app_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/app_data_backup.tar.gz /data
```

### Seed with demo data

A `seed` service is included for quickly loading realistic test data (users,
customers, repairs). It is gated behind a Compose profile so it never runs
unless explicitly requested.

```bash
# Load demo data (skips silently if data already exists)
docker compose run --rm seed

# Wipe all seeded rows and re-seed from scratch
docker compose run --rm seed --reset
```

Demo credentials created by the seed: `admin` / `admin123` and
`hans.mueller` / `test123`.

## Development

The project uses a Dev Container (VS Code) with MariaDB, Python, and Node
pre-configured.

```bash
# After the container starts:
cd app && python run_migrations.py   # create tables
cd app && python seed_dev.py         # load test data
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for the full setup guide, API reference,
and model documentation.

## Versioning

Releases follow [Semantic Versioning](https://semver.org/) and are managed
with [Release Please](https://github.com/googleapis/release-please).
The current version is stored in `VERSION` and kept in sync with
`frontend/package.json` and `.release-please-manifest.json`.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, TypeScript, Vuetify 3, Pinia, Vite |
| Backend | Python 3, Flask, SQLAlchemy, Flask-Login |
| Database | MariaDB / MySQL |
| PDF generation | PyMuPDF (fitz) |
| Container | Docker, Docker Compose |

## Acknowledgments
This projejct is based on the great work of [atec111](https://gitlab.com/atec111) over on gitlab