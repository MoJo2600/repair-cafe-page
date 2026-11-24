# RepairCafePage

Web application for running repair café events: device intake with a signed
liability waiver, a work log per repair, electrical safety testing (VDE), QR-code
labels and statistics. Built for the workshop — tablets and a shared PC — and
self-hosted with Docker on a Raspberry Pi or any Linux server.

## Features

- **Intake** — customer, device, category and defect; liability waiver signed
  on screen or uploaded as PDF; optional device photo
- **Repair workflow** — status Offen → In Bearbeitung → Repariert / Nicht Repariert,
  assignee, work log with photos and attachments, celebration on success
- **QR codes and labels** — every repair has a QR code; scanning it opens the repair.
  Labels can be printed on a Seiko SLP 650 via CUPS
- **VDE testing** — record DIN VDE 0701/0702 results and download a filled
  Prüfprotokoll PDF
- **Cancellation** — customer signs a cancellation form when a repair is aborted
- **Customers** — reusable contact records across repairs
- **Login** — local accounts or SSO via any OIDC provider; helpers switch on a shared
  PC by PIN (workshop network only)
- **Admin settings** — dropdown values, test devices, organisation name, logo,
  disclaimer / cancellation templates, celebration sound
- **Dashboard and statistics**, XLSX export, optional scheduled CSV export by e-mail

## Quick start

Requirements: Docker with Compose v2.

```bash
git clone https://github.com/MoJo2600/repaircafepage.git
cd repaircafepage
cp .env.example .env
$EDITOR .env            # set passwords, FLASK_SECRET_KEY (openssl rand -hex 32), PUBLIC_URL
docker compose up -d
docker compose logs backend | grep -A3 "INITIAL ADMIN"   # generated admin password
```

The app runs at `http://<host>`. Database migrations run automatically on every
backend start.

Next steps: [deployment guide](docs/DEPLOYMENT.md) (updates, backups, HTTPS),
[configuration reference](docs/CONFIGURATION.md),
[SSO and PINs](docs/AUTHENTICATION.md),
[label printer](docs/CUPS_NETWORK_SETUP.md).

## Documentation

All documentation lives in [`docs/`](docs/README.md):

| For | Read |
|---|---|
| Running the app | [Deployment](docs/DEPLOYMENT.md) · [Configuration](docs/CONFIGURATION.md) · [Authentication](docs/AUTHENTICATION.md) · [Label printer](docs/CUPS_NETWORK_SETUP.md) |
| Working on the code | [Development](docs/DEVELOPMENT.md) · [Architecture](docs/ARCHITECTURE.md) · [API](docs/API.md) · [UI style guide](docs/STYLEGUIDE.md) |
| Plans | [Feature ideas](docs/FEATURE_IDEAS.md) · [Known bugs](docs/KNOWN_BUGS.md) |

Release notes: [CHANGELOG.md](CHANGELOG.md).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, TypeScript, Vuetify 4, Pinia, vue-router, Vite |
| Backend | Python 3.12, Flask, SQLAlchemy, Alembic, Pydantic v2, Flask-Login, Authlib |
| Database | MariaDB 11 |
| Documents | PyMuPDF (PDF), Pillow + qrcode (labels), openpyxl (XLSX) |
| Runtime | Docker Compose: nginx, Gunicorn, MariaDB; multi-arch images (amd64, arm64) |

## Versioning

Releases follow [Semantic Versioning](https://semver.org/) and are created by
[Release Please](https://github.com/googleapis/release-please) from
[Conventional Commits](https://www.conventionalcommits.org/). The version lives in
`VERSION`, `frontend/package.json` and `.release-please-manifest.json`.

## Acknowledgments

This project is based on the work of [atec111](https://gitlab.com/atec111) on GitLab.
