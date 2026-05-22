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

# Pull and start
docker compose up -d

# Run database migrations (first start and after every update)
docker compose exec app python run_migrations.py
```

The app is available at `http://<host>:5000`.

### Update

```bash
docker compose pull
docker compose up -d
docker compose exec app python run_migrations.py
```

### Stack overview

| Container | Image | Exposed port |
|---|---|---|
| `app` | `ghcr.io/mojo2600/repaircafepage:latest` | 5000 |
| `db` | `mariadb:11` | internal only |

The image ships a multi-arch manifest (`linux/amd64` + `linux/arm64`) so the
same `docker compose up -d` command works on a Raspberry Pi 4 or 5 without
changes.

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