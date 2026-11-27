# Deployment

How to run RepairCafePage in production with Docker Compose, keep it updated and
back it up. For every environment variable see [CONFIGURATION.md](CONFIGURATION.md).

## Stack

| Container | Image | Role | Port |
|---|---|---|---|
| `frontend` | `ghcr.io/mojo2600/repaircafepage-frontend` | nginx: serves the Vue app, proxies `/api/` to the backend | 80 |
| `backend` | `ghcr.io/mojo2600/repaircafepage-backend` | Gunicorn + Flask: API, PDFs, labels, e-mail | internal 5000 |
| `db` | `mariadb:11` | database | internal |

Images are published for `linux/amd64` and `linux/arm64` (Raspberry Pi 4/5) with the
tags `latest`, the release version (e.g. `v1.7.0`) and `dev` (every push to `main`).

Both containers run as unprivileged users. The backend runs as uid 1000.

## Install

Requirements: Docker with Compose v2.

```bash
git clone https://github.com/MoJo2600/repaircafepage.git
cd repaircafepage
cp .env.example .env
```

Edit `.env`. At minimum:

| Variable | Value |
|---|---|
| `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` | two different strong passwords |
| `FLASK_SECRET_KEY` | `openssl rand -hex 32` — the backend refuses to start with the placeholder or a key shorter than 32 characters |
| `PUBLIC_URL` | the URL people open in the browser, e.g. `https://repairs.example.org` |
| `SESSION_COOKIE_SECURE` | `true` when served over HTTPS |

Start with the published images:

```bash
docker compose pull
docker compose up -d
```

`compose.yaml` also contains `build:` sections, so `docker compose up -d --build`
builds the images from the checked-out source instead.

On start the backend:

1. runs all pending database migrations (`entrypoint.backend.sh`),
2. creates an admin account `admin` if no admin exists and prints its random password
   to the log,
3. checks that `PIN_MODE` matches the database (see [AUTHENTICATION.md](AUTHENTICATION.md#switching-pin-mode)).

```bash
docker compose logs backend | grep -A3 "INITIAL ADMIN"
```

Log in, change the password, then set up the organisation in **Einstellungen**:
name, website, app URL (used in label QR codes), logo, dropdown values, test devices
and the disclaimer / cancellation PDF templates.

### HTTPS and reverse proxy

The frontend container speaks plain HTTP on port 80. For HTTPS put a reverse proxy in
front of it (e.g. Nginx Proxy Manager, Traefik, Cloudflare Tunnel) and set:

```dotenv
PUBLIC_URL=https://repairs.example.org
SESSION_COOKIE_SECURE=true
```

The backend trusts one proxy hop for `X-Forwarded-For/-Proto/-Host`.

Camera features (QR scanner, device photos) need a secure context, i.e. HTTPS or
`localhost`.

Requests that arrive through Cloudflare are treated as "outside the workshop": no PIN
lock and no PIN unlock. See [AUTHENTICATION.md](AUTHENTICATION.md#pin-lock-and-unlock).

### Label printer

Optional. The backend prints through the host's CUPS daemon via the mounted socket
`/run/cups/cups.sock`. CUPS must be running on the host **before** the backend starts,
otherwise Docker creates an empty directory in place of the socket. Setup guide:
[CUPS_NETWORK_SETUP.md](CUPS_NETWORK_SETUP.md).

If you don't use a printer and the host has no CUPS, remove the
`/run/cups/cups.sock` volume line from `compose.yaml`.

### Scheduled e-mail export

`EMAIL_ENABLED=true` with the Mailtrap settings enables `GET /api/mailexport`
(admin only), which sends all repairs as CSV in a password-protected ZIP. The
built-in schedule (third Saturday of the month, 20:00) only runs when the backend is
started with `START_SCHEDULER=1`; the supplied `compose.yaml` does not set it.

## Configuration changes

The backend reads its environment only at container creation. After editing `.env`:

```bash
docker compose up -d --force-recreate backend
```

## Update

```bash
git pull                  # updated compose.yaml / .env.example, if any
docker compose pull
docker compose up -d
```

Migrations run automatically. Check [CHANGELOG.md](../CHANGELOG.md) for upgrade notes,
and compare your `.env` against `.env.example` for new variables.

## Persistent data

| Location | Contents |
|---|---|
| volume `db_data` | MariaDB database |
| volume `app_data` → `/data` | signed disclaimers and cancellations, attachments and photos, uploaded templates, logo and celebration sound |
| `./config` → `/config` (read-only) | bundled sample templates (`Disclaimer_sample.pdf`, `Cancellation_sample.pdf`) |

Uploaded templates in `/data` take precedence over the samples in `/config`.

If you switch `/data` to a bind mount whose files belong to root, run
`chown -R 1000:1000 <dir>` once on the host.

## Backup and restore

The volume names are prefixed with the Compose project name (by default the
directory name, e.g. `repaircafepage_app_data`); check with `docker volume ls`.

```bash
# Database
docker compose exec db sh -c 'mariadb-dump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > backup.sql

# Files
docker run --rm -v repaircafepage_app_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/app_data.tar.gz -C /data .
```

Restore:

```bash
docker compose exec -T db sh -c 'mariadb -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' < backup.sql

docker run --rm -v repaircafepage_app_data:/data -v "$PWD":/backup alpine \
  tar xzf /backup/app_data.tar.gz -C /data
```

Back up `.env` too: without the same `FLASK_SECRET_KEY` all stored PINs become invalid.

## Admin password reset

Open a shell in the backend container (`docker compose exec backend sh`, or in Dockge
the terminal icon of the `backend` service) and run:

```sh
reset-admin-password                 # account "admin", prompts for the new password (min. 12 characters)
reset-admin-password --generate      # print a random password instead
reset-admin-password --user NAME     # another local admin account
```

The account is reactivated, or recreated if it was deleted. SSO accounts are refused.
Nothing is written to the logs. The old `RESET_ADMIN_PASSWORD` variable is ignored.

## Health check

`GET /api/healthz` returns 200 without login.

## Troubleshooting

| Symptom | Check |
|---|---|
| Backend restarts with `FLASK_SECRET_KEY must be a random value…` | set a real key (`openssl rand -hex 32`), then recreate the backend |
| Backend stops with a `PIN_MODE` error | see [AUTHENTICATION.md](AUTHENTICATION.md#switching-pin-mode) |
| Login works but you are logged out immediately | `SESSION_COOKIE_SECURE=true` while serving plain HTTP |
| SSO redirect fails | `PUBLIC_URL` must match the browser URL; redirect URI `<PUBLIC_URL>/api/auth/oidc/callback` |
| Label QR codes point to `localhost` | set the app URL in **Einstellungen** |
| `Permission denied` under `/data` | files owned by root, see [Persistent data](#persistent-data) |
| Uploads fail with 413 | nginx accepts at most 25 MB per request |
