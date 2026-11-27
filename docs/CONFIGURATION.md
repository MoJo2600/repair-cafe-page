# Configuration

The backend is configured through environment variables. With Docker Compose they go
into `.env` (template: [`.env.example`](../.env.example)) and are passed on in
[`compose.yaml`](../compose.yaml). Recreate the backend after a change:
`docker compose up -d --force-recreate backend`.

Values that admins change at runtime (organisation name and website, app URL for QR
codes, logo, PDF templates, celebration sound, dropdown values, test devices) are not
environment variables; they live in the database and `/data` and are edited under
**Einstellungen**.

Defaults below are the application defaults. Where `compose.yaml` passes a different
default, it is noted.

## Database

| Variable | Default | Purpose |
|---|---|---|
| `MYSQL_HOST` | `db` | MariaDB host |
| `MYSQL_PORT` | `3306` | port (migrations only; the app always uses 3306) |
| `MYSQL_DATABASE` | `repaircafepage` | database name |
| `MYSQL_USER` | `root` (compose: `repaircafe`) | user |
| `MYSQL_PASSWORD` | `mariadb` | password — always set it |
| `MYSQL_ROOT_PASSWORD` | — | MariaDB root password, used by the `db` container only |
| `DATABASE_URL` | — | full SQLAlchemy URL; overrides all `MYSQL_*` (used by tests, e.g. `sqlite://`) |

The `MYSQL_*` values create the database and user on the first start of an empty
`db_data` volume. Changing them later does not change the existing accounts.

## Application

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_SECRET_KEY` | — | **required in production.** Signs sessions and keys the PIN hashes. At least 32 characters; generate with `openssl rand -hex 32`. Changing it logs everyone out and invalidates all PINs |
| `FLASK_ENV` | `prod` (compose: `production`) | `development`/`dev` enables debug mode and a random secret key if none is set |
| `PUBLIC_URL` | empty | URL as seen by the browser, without trailing slash. Required for SSO |
| `SESSION_COOKIE_SECURE` | `true` in production, `false` in development | `true` for HTTPS. Over plain HTTP set `false` (compose default), or the session cookie is never sent back |
| `DATA_DIR` | `<repo>/data` (container: `/data`) | persistent attachments, uploaded templates and other files |
| `CONFIG_DIR` | `<repo>/config` (container: `/config`) | bundled sample PDF templates |
| `CORS_ORIGINS` | empty | comma-separated exact origins for a separately hosted frontend. Not needed with the nginx / Vite proxy; not forwarded by `compose.yaml` |
| `START_SCHEDULER` | unset | `1` starts the background scheduler (monthly e-mail export) |
| `CREATE_TABLES_ON_STARTUP` | unset | `1` runs `db.create_all()` on start. Not needed; migrations create the schema |

### Legacy signed-document migration

Before Gunicorn starts, `app/migrate_legacy_documents.py` copies existing PDFs
from `DATA_DIR/signed_disclaimers` and `DATA_DIR/signed_cancellations` into the
unified attachment store and creates or repairs the corresponding database rows.
The operation is idempotent, byte-verified and leaves the source PDFs untouched.

For this one-time migration, `SIGNED_PDF_STORAGE_PATH` and
`SIGNED_CANCELLATION_STORAGE_PATH` can override the default legacy source
directories. They are not Flask runtime configuration and are not used for new
documents. After verifying the migration and backing up the retained originals,
the old directories can be archived or removed.

## Login (OIDC / SSO)

SSO is enabled when `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` and
`PUBLIC_URL` are all set. Details and claim behaviour: [AUTHENTICATION.md](AUTHENTICATION.md).

| Variable | Default | Purpose |
|---|---|---|
| `OIDC_ISSUER` | empty | issuer URL (discovery at `<issuer>/.well-known/openid-configuration`) |
| `OIDC_CLIENT_ID` | empty | client ID |
| `OIDC_CLIENT_SECRET` | empty | client secret |
| `OIDC_SCOPES` | `openid email profile` | space-separated scopes |
| `OIDC_ADMIN_CLAIM` | `repaircafe_admin` | boolean admin claim; empty disables the mapping |
| `OIDC_GROUPS_CLAIM` | `groups` | group-list claim; empty disables it |
| `OIDC_DENIED_GROUPS` | empty | comma-separated groups whose login is refused |
| `OIDC_PIN_CLAIM` | `pin_code` | six-digit PIN claim (only with `PIN_MODE=oidc`) |

## PINs

| Variable | Default | Purpose |
|---|---|---|
| `PIN_MODE` | `oidc` (`.env.example`: `local`) | `local`: users generate their PIN in the profile. `oidc`: PIN comes from the identity provider |
| `PIN_MODE_RESET_ACK` | empty | `oidc-to-local` or `local-to-oidc` to confirm a mode switch, which deletes all PINs |
| `PIN_MAX_FAILED_PER_SESSION` | `5` | wrong PINs per browser session before it is logged out (60 s pause after every 3) |
| `PIN_MAX_FAILED_PER_ACCOUNT` | `5` | wrong PINs per primary login account within the window |
| `PIN_MAX_FAILED_GLOBAL` | `15` | wrong PINs across all sessions within the window; then PIN unlock pauses for everyone |
| `PIN_RATE_WINDOW_MINUTES` | `15` | window for the account and global limits |

## Password login limits

Counted in memory per Gunicorn worker (the image runs one worker).

| Variable | Default | Purpose |
|---|---|---|
| `LOGIN_MAX_FAILED_PER_IP` | `10` | failed logins per client IP within the window |
| `LOGIN_MAX_FAILED_PER_USER` | `5` | failed logins per username within the window |
| `LOGIN_RATE_WINDOW_MINUTES` | `15` | window |

## Label printer

Setup: [CUPS_NETWORK_SETUP.md](CUPS_NETWORK_SETUP.md).

| Variable | Default | Purpose |
|---|---|---|
| `LABEL_PRINTER_ENABLED` | `false` | shows the print button and enables `POST /api/repairs/<id>/print-label` |
| `LABEL_PRINTER_NAME` | `SLP650` | CUPS queue name on the host (`lpstat -p`) |
| `CUPS_SERVER` | unset | read by `lp` itself: send jobs directly to a CUPS server on the LAN (e.g. `192.168.178.223:631`) instead of the host socket |

## E-mail export (Mailtrap)

| Variable | Default | Purpose |
|---|---|---|
| `EMAIL_ENABLED` | `false` | enables `GET /api/mailexport` and the scheduled export |
| `MAIL_TOKEN` | — | Mailtrap API token |
| `MAIL_SENDER` | — | verified sender address |
| `MAIL_SENDER_NAME` | `RepairCafe` | sender name |
| `EXPORT_MAIL_RECEIVER` | — | recipient of the export |
| `ZIP_PASSWORD` | `password` | password of the ZIP attachment — always set it when e-mail is enabled |

## Logging (Grafana Loki)

Optional. Enabled when all three are set.

| Variable | Purpose |
|---|---|
| `GCLOUD_HOSTED_LOGS_ID` | Loki user ID |
| `GCLOUD_PROM_API_KEY` | API key |
| `GCLOUD_HOSTED_LOGS_URL` | Loki push URL without scheme |
