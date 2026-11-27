# Architecture

How RepairCafePage is put together. For running it see
[DEPLOYMENT.md](DEPLOYMENT.md), for working on it [DEVELOPMENT.md](DEVELOPMENT.md).

## Overview

```
                    Production (Docker Compose)

 Browser / tablet ──HTTP──► frontend (nginx :80)
                              ├─ /            Vue SPA (static build)
                              └─ /api/  ──►  backend (Gunicorn + Flask :5000)
                                               ├─ MariaDB (db)
                                               ├─ /data   attachments, uploaded templates and files
                                               ├─ /config sample PDF templates (read-only)
                                               └─ /run/cups/cups.sock ──► host CUPS ──► label printer
```

In development Vite (port 5173) serves the SPA with hot reload and proxies `/api` to
Flask on port 5000, so the browser sees one origin in both setups.

The frontend is a single-page app; the backend is a JSON API under `/api`. Flask
serves no HTML pages.

## Backend

Flask app factory in `app/__init__.py`. On creation it loads the configuration,
initializes SQLAlchemy, Flask-Login, Swagger and the OIDC client, attaches the PDF and
label services, registers the blueprints (all under `/api`), and then ensures an admin
exists and the PIN mode matches the database.

Production runs `wsgi.py` in Gunicorn with **one worker and four threads**. The login
rate limiter keeps its counters in that worker's memory.

### Request pipeline

Every `/api` request passes two `before_request` hooks:

1. **Cross-site check** — `POST/PUT/PATCH/DELETE` must come from the same origin
   (`app/auth/csrf.py`), otherwise 403.
2. **Auth guard** — every endpoint requires a logged-in session unless the view is
   marked `@public_endpoint` (login, OIDC, auth config, health, logo, celebration sound).
   Then:
   - no session → **401** `Authentication required`
   - the session's PIN grant does not belong to the current user → **401**
     `Primary login required`
   - session idle for more than 60 s inside the workshop network → **423**
     `Session locked` (the frontend shows the PIN lock screen)

Admin-only endpoints additionally use `@admin_required`. Request bodies are validated
with `@validate_request(PydanticSchema)`; validation errors return 400 with
`{reply: "error", error, details}`.

All responses get `Cache-Control: no-store`.

### Authentication

Flask-Login sessions, created by password login or OIDC (Authlib). After a primary
login, a `pin_unlock_sessions` row tracks which helper is currently active in that
browser, whether it is locked, its last activity and failed PIN attempts. Details:
[AUTHENTICATION.md](AUTHENTICATION.md).

### Services

| Module | Does |
|---|---|
| `services/document_service.py` | sanitizes versioned HTML, renders escaped placeholders, and produces WeasyPrint PDFs |
| `services/pdf_service.py` + `imports/pdfsigner.py` | compatibility support for uploaded AcroForm PDF templates |
| `services/vde_pdf_service.py` | renders the VDE Prüfprotokoll PDF |
| `services/label_service.py` | renders the label PNG and prints it with `lp` |
| `services/export_service.py`, `web/routes.py` | XLSX export, CSV for the e-mail export |
| `services/email_service.py` | sends the export as password-protected ZIP via Mailtrap |
| `services/pin_service.py`, `pin_unlock_service.py` | PIN hashing, PIN mode, lock / unlock, limits |
| `services/login_rate_limit.py` | password login limits |
| `tasks/scheduler.py` | APScheduler job for the monthly e-mail export (only with `START_SCHEDULER=1`) |

## Data model

```
customers 1──* repairs *──1 settings (repair_type)
                 │  *──1 users (user_id = assignee, created_by_id)
                 ├──* repair_logs *──1 users
                 ├──* vde_tests
                 └──* repair_attachments ──0..1 repair_logs
                                               └──0..1 document_template_versions *──1 document_templates
users 1──* pin_unlock_sessions
pin_state (one row: active PIN mode)   pin_unlock_failures   app_config (key/value)
```

| Table | Holds |
|---|---|
| `users` | local and SSO accounts: username, name, e-mail, password hash, `is_admin`, `is_active`, `oidc_sub`, `pin_code_hash` |
| `customers` | first and last name, phone, e-mail; reused across repairs |
| `repairs` | intake date, device (`geraet_art`), category (`repair_type_id` → settings), defect, disclaimer-signed flag (the raw signature is transient), VDE flag (`din_pruef`), `status` / `status_detail`, assignee, repair description, `closed_at`, handover timestamp/user, `qr_token` |
| `repair_logs` | timeline of a repair: `log_type` `work` (description, duration), `status_change` (`status_from` → `status_to`), `assignee_change` or `handover_change` |
| `vde_tests` | DIN VDE 0701/0702 results: visual check, protective conductor, insulation, leakage current, overall result, tester, device |
| `document_templates` | the two fixed editable document roles `disclaimer` and `cancellation` |
| `document_template_versions` | immutable sanitized HTML revisions; a published version is active per template |
| `repair_attachments` | files of a repair: `device_photo` (at most one), `log_entry`, `disclaimer`, `cancellation`, `misc`; generated PDFs pin a template version |
| `settings` | admin-managed dropdown values by `category`: `repair_type`, `test_device` (with serial number) |
| `app_config` | organisation name, website, app URL for QR codes |
| `pin_state`, `pin_unlock_sessions`, `pin_unlock_failures` | PIN mode and PIN lock state |

Models: `app/models.py`. Schema changes go through Alembic migrations in
`app/migrations/versions/`, applied on every backend start.

### Files

Everything that is not in the database lives under `DATA_DIR` (`/data`):

| Path | Contents |
|---|---|
| `attachments/<repair_id>/` | device photos, log photos, generated/uploaded customer PDFs, other files |
| `disclaimer.pdf`, `cancellation.pdf` | uploaded templates (otherwise the samples from `CONFIG_DIR` are used) |
| `logo.png` | uploaded logo (otherwise `app/static/logo.jpg`) |
| `celebration.mp3` | uploaded celebration sound (otherwise `app/static/fanfare.mp3`) |

Customer PDFs are stored as `RepairAttachment` rows below
`attachments/<repair_id>/`. On backend startup, the legacy migration command
non-destructively copies any remaining `signed_disclaimers/<id>.pdf` and
`signed_cancellations/<id>.pdf` files into that store and creates or repairs the
database rows. The source files are retained; they are not read by the running
application. Deleting a repair removes only its unified attachment directory.

## Repair status model

Each repair has a **status** and an optional **status detail**.

| Status | Meaning | Allowed details |
|---|---|---|
| Offen | waiting, nobody working on it | — |
| In Bearbeitung | being repaired | — |
| Repariert | finished successfully | — |
| Nicht Repariert | finished without success | **required**: Nicht moeglich, Abbruch, Wartezeit zu lang |

Allowed transitions:

| From | To |
|---|---|
| Offen | In Bearbeitung |
| In Bearbeitung | Offen, Repariert, Nicht Repariert |
| Repariert | Offen, In Bearbeitung, Nicht Repariert |
| Nicht Repariert | Offen, In Bearbeitung |

Rules enforced by `PUT /api/repairs/<id>`:

- In Bearbeitung needs an assignee.
- Repariert and Nicht Repariert need a repair description.
- Closing sets `closed_at`; reopening clears it; back to Offen also clears the assignee.
- Every status or assignee change writes a `repair_logs` entry in the same transaction.

In the UI, "Nicht Repariert / Abbruch" asks the customer to sign the cancellation
form, and closing as Repariert offers a VDE test — it is mandatory when the last VDE
test of the repair failed.

Closing a repair does not imply customer pickup. A closed repair without
`handed_over_at` is "Zur Abholung bereit"; recording the timestamp marks it as handed
over. The handover can be reset, and reopening a repair clears it automatically.
Existing closed records are initialized as handed over by migration `018`.
The feature is disabled by default and can be enabled by administrators under
**Einstellungen → Allgemein**. Both the frontend surfaces and handover API endpoints
honor the setting. When enabled, the dashboard and PIN lock screen also show the
anonymous repair IDs and categories of devices ready for pickup.

The rules exist twice and must stay in sync: `app/schemas.py`
(`VALID_REPAIR_STATUSES`, `VALID_STATUS_DETAILS`), `app/api/repairs.py`
(`STATUS_TRANSITIONS`) and `frontend/src/domain/repairStatus.ts`. To add a detail value,
change all three and add tests.

## Frontend

Vue 3 + TypeScript + Vuetify 4, built by Vite and served by nginx. Code layout:
[DEVELOPMENT.md](DEVELOPMENT.md#frontend).

| Route | Page | Access |
|---|---|---|
| `/login` | login (password and/or SSO) | public |
| `/lock` | PIN lock screen with dashboard and keypad | locked session |
| `/` | overview: next repair, open / in progress / done | login |
| `/dashboard` | statistics (also shown on the lock screen) | login |
| `/repairs` | repair list with search and filters | login |
| `/create-repair` | intake: customer, device, photo, signature | login |
| `/edit/:qrToken` | repair page: status, assignee, log, VDE, attachments, label | login |
| `/customers` | customers | login |
| `/profile` | own profile and PIN | login |
| `/users`, `/settings`, `/styleguide` | user management, settings, living style guide | admin |

The router guard sends unauthenticated users to `/login` and locked sessions to
`/lock`, keeping the target in the query. QR codes contain
`<app URL>/edit/<qr_token>`; scanning one with the in-app scanner or a phone opens the
repair after login.

State:

- `authStore` — current user, PIN session, lock state.
- `repairStore` — the repair list, refreshed every 10 s, plus the status actions
  ([`stores/README.md`](../frontend/src/stores/README.md)).
- `usePinSession()` — idle lock, activity heartbeats and cross-tab sync
  (BroadcastChannel).

### API contract

```
app/schemas.py + route docstrings
      │  python scripts/dump_openapi_spec.py
      ▼
frontend/openapi.json (Swagger 2.0, committed)
      │  pnpm generate-api (swagger-typescript-api)
      ▼
frontend/src/api/generated/ ──► api (src/api/client.ts): 401 → login, 423 → lock screen
```

CI fails if either generated file is out of date. See [API.md](API.md).

## Label printing

```
POST /api/repairs/<id>/print-label
  → LabelService: PNG 602 × 330 px (51 × 28 mm at 300 dpi)
      date, customer, device, QR code (<app URL>/edit/<qr_token>), #id, logo, organisation
  → lp -d $LABEL_PRINTER_NAME label.png
  → /run/cups/cups.sock (mounted from the host; /etc/cups/client.conf in the image)
  → host CUPS queue ──► USB printer, or IPP relay to a print server (e.g. Raspberry Pi)
```

The app URL comes from **Einstellungen**, falling back to the request's host. Setup:
[CUPS_NETWORK_SETUP.md](CUPS_NETWORK_SETUP.md).
