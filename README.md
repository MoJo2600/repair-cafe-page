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
- **Status tracking** — Offen → In Bearbeitung → Repariert / Nicht Repariert
- **User management** — admin and repairer accounts with session-based auth
- **Settings** — configurable dropdown values (repair types, test devices)
  managed through the UI
- **Data export** — XLSX download (`/api/export`, admin only); optional CSV e-mail delivery

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

### OIDC and Profile PINs

Any OIDC provider supporting discovery and the authorization-code flow can be
configured with `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, and
`PUBLIC_URL` (the browser-facing application URL). Register
`<PUBLIC_URL>/api/auth/oidc/callback` as the redirect URI. Use HTTPS and
`SESSION_COOKIE_SECURE=true` in production. While SSO is enabled, password
login remains available only to local administrators as a break-glass option.
Login always requests fresh authentication (`prompt=login`) for shared PCs.

| Variable | Default | Purpose |
| --- | --- | --- |
| `OIDC_SCOPES` | `openid email profile` | Space-separated scopes |
| `OIDC_ADMIN_CLAIM` | `repaircafe_admin` | Boolean admin claim; absent/false means non-admin |
| `OIDC_GROUPS_CLAIM` | `groups` | Group-list claim |
| `OIDC_DENIED_GROUPS` | empty | Comma-separated denied groups |
| `OIDC_PIN_CLAIM` | `pin_code` | Six-digit PIN claim used in OIDC PIN mode |
| `PIN_MODE` | `oidc` | `oidc` or `local`, never both |

Claim mappings refer to top-level claims. Optional mappings can be disabled
with an empty name. Standard `sub`, `email`, `name`, and `preferred_username`
claims retain their normal meaning. An admin claim must be boolean `true`
or the string `true`; arbitrary nonempty strings never grant admin rights.
Changing to another issuer for an existing database requires a deliberate
identity/account migration: subjects are not automatically re-linked across issuers.

**Local PIN mode:** set `PIN_MODE=local`. Users sign in normally, open their
profile using their account name in the sidebar, and explicitly generate a
PIN. No PIN is created by logging in or simply opening the profile. PINs are
random six-digit values, including possible leading zeroes. Each PIN is shown
only in its creation response and cannot be retrieved later; a forgotten PIN
must be replaced with confirmation. A database unique constraint and collision
retries prevent duplicate PINs. Provider PIN claims are ignored in this mode.

**OIDC PIN mode:** set `PIN_MODE=oidc`. PINs are refreshed from the configured
claim at each SSO login. Profile generation/replacement is disabled, including
through the API. Users retrieve their PIN from their identity provider, such
as their easyVerein profile. Missing/invalid claims clear the previous PIN but
do not block normal SSO login. A reassigned provider PIN is removed from its
previous holder, preserving one owner per PIN. There is no local fallback.

For the existing easyVerein integration through Authentik, explicitly set:

```dotenv
PIN_MODE=oidc
OIDC_SCOPES=openid email profile repaircafe
OIDC_PIN_CLAIM=door_code
OIDC_ADMIN_CLAIM=repaircafe_admin
OIDC_GROUPS_CLAIM=groups
OIDC_DENIED_GROUPS=Kind
```

For a standard provider without a PIN claim, use `PIN_MODE=local` with the
standard scopes. Configure its admin/group mappings as needed, or leave them
empty. The supplied `.env.example` selects local mode explicitly.

**Upgrade:** migration 012 renames `door_code_hash` to `pin_code_hash` and
preserves existing keyed hashes. Duplicate legacy hashes stop migration with
an actionable error instead of choosing an owner. Configure the explicit
easyVerein mappings above before upgrading that setup: generic defaults no
longer request the `repaircafe` scope or read `door_code` automatically.
Existing provider hashes are tracked as OIDC-owned; they cannot silently
become local PINs.

**Changing modes deletes all existing PINs.** Back up the database and stop
all backend instances before switching. Startup refuses the change unless
`PIN_MODE_RESET_ACK` matches the exact transition:

```dotenv
PIN_MODE=local
PIN_MODE_RESET_ACK=oidc-to-local
```

Use `local-to-oidc` for the reverse transition. Start the backend with the new
settings, then remove the acknowledgement. The PIN reset and persisted mode
change are atomic and applied once; subsequent restarts do not erase newly
issued PINs. Accounts and sessions are not deleted. Local users generate new
PINs explicitly; provider PINs return at the next successful SSO login.
Do not run old-mode and new-mode instances together; PIN operations fail
closed if the persisted mode differs from the process configuration.

PINs are stored only as server-keyed hashes, never plaintext or reversible
encryption. Keep `FLASK_SECRET_KEY` stable: changing it invalidates existing
PIN hashes as well as sessions. Treat changes to the PIN claim's meaning as
a credential migration, not a cosmetic rename. Profile PIN responses are
uncacheable and PINs are never included in user-list or normal profile data.

This release prepares PIN storage and profile management only. A PIN login
endpoint, lock screen, and unlock flow are not implemented yet.


### Deploy with Docker Compose

compose.yml

```yaml
services:
  frontend:
    image: ghcr.io/mojo2600/repair-cafe-page-frontend:latest
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    image: ghcr.io/mojo2600/repair-cafe-page-backend:latest
    restart: unless-stopped
    environment:
      FLASK_ENV: production
      MYSQL_HOST: db
      MYSQL_DATABASE: ${MYSQL_DATABASE:-repaircafedb}
      MYSQL_USER: ${MYSQL_USER:-repaircafe}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      FLASK_SECRET_KEY: ${FLASK_SECRET_KEY}
      SESSION_COOKIE_SECURE: "false"     # set "true" if HTTPS terminates upstream
      PUBLIC_URL: ${PUBLIC_URL:-}
      OIDC_ISSUER: ${OIDC_ISSUER:-}
      OIDC_CLIENT_ID: ${OIDC_CLIENT_ID:-}
      OIDC_CLIENT_SECRET: ${OIDC_CLIENT_SECRET:-}
      OIDC_SCOPES: ${OIDC_SCOPES-openid email profile}
      OIDC_PIN_CLAIM: ${OIDC_PIN_CLAIM-pin_code}
      OIDC_ADMIN_CLAIM: ${OIDC_ADMIN_CLAIM-repaircafe_admin}
      OIDC_GROUPS_CLAIM: ${OIDC_GROUPS_CLAIM-groups}
      OIDC_DENIED_GROUPS: ${OIDC_DENIED_GROUPS:-}
      PIN_MODE: ${PIN_MODE-oidc}
      PIN_MODE_RESET_ACK: ${PIN_MODE_RESET_ACK:-}
      EMAIL_ENABLED: "false"
      MAIL_TOKEN: ""
      MAIL_SENDER: ""
      MAIL_SENDER_NAME: RepairCafe
      EXPORT_MAIL_RECEIVER: ""
      ZIP_PASSWORD: ${ZIP_PASSWORD:-}

    extra_hosts:
      - "host-gateway:host-gateway"
    volumes:
      - app_data:/data
      # Uncomment to enable label printing (see § Setup Label printer):
      # - /run/cups/cups.sock:/run/cups/cups.sock
    depends_on:
      db:
        condition: service_healthy

  db:
    image: mariadb:11
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: ${MYSQL_DATABASE:-repaircafedb}
      MYSQL_USER: ${MYSQL_USER:-repaircafe}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

volumes:
  db_data:
  app_data:
```

.env

```bash
# Database MYSQL_DATABASE=repaircafepage
MYSQL_USER=repaircafe
MYSQL_PASSWORD=change_me
MYSQL_ROOT_PASSWORD=change_me_root

# Flask secret key for session signing – use a long random string in production.
FLASK_SECRET_KEY=change_me_secret
```

Database migrations run automatically on first backend startup — no manual
step is needed.

An **initial admin account** (`admin`) is created automatically on first
startup if no admin exists. The generated password is printed to the backend
logs. To reset a forgotten admin password, set `RESET_ADMIN_PASSWORD=true`
in the backend environment and restart — a new password will be logged.
Remove the variable afterwards.

### Update

```bash
docker compose pull
docker compose up -d
# Migrations run automatically on backend startup — no manual step needed.
```

### Hardware

#### Setup Label printer

The backend can print QR-code labels on a **SII SLP 650** label printer.
Printing is routed through the host machine's CUPS daemon via a mounted Unix
socket — no network port configuration needed.

**1. Install the SLP 650 driver on the host**

```bash
git clone https://github.com/fawkesley/smart-label-printer-slp-linux-driver.git
cd smart-label-printer-slp-linux-driver/src
make && sudo make install
```

Add the printer in your system's printer settings (CUPS queue name: `SLP650`).

**2. Allow the Docker container to access CUPS**

Edit `/etc/cups/cupsd.conf` on the host and add the Docker bridge network to
the allowed list:

```
<Location />
  Order allow,deny
  Allow localhost
  Allow from 172.17.0.0/16
</Location>
```

Then restart CUPS: `sudo systemctl restart cups`

**3. Mount the CUPS socket and enable printing in `compose.yaml`**

Uncomment the socket volume and set the two env vars:

```yaml
services:
  backend:
    environment:
      LABEL_PRINTER_ENABLED: "true"
      LABEL_PRINTER_NAME: "SLP650"   # must match the CUPS queue name
    volumes:
      - /run/cups/cups.sock:/run/cups/cups.sock
```

Or add to your `.env`:

```bash
LABEL_PRINTER_ENABLED=true
LABEL_PRINTER_NAME=SLP650
```

Restart the stack: `docker compose up -d backend`

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