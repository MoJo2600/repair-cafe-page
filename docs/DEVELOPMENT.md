# Development

How to run, test and change the code. How the pieces fit together:
[ARCHITECTURE.md](ARCHITECTURE.md).

## Setup

The project is set up as a VS Code **Dev Container** (Python 3, Node, pnpm, MariaDB,
Adminer, CUPS client). Open the folder in VS Code and choose *Reopen in Container*;
Python and frontend dependencies are installed on creation.

Initialize the development database once:

```bash
bash dev-start.sh --setup
```

This creates the database `repaircafepage_dev`, runs the migrations and loads test
data. It never drops or resets anything; seeding is skipped if the test users exist.
VS Code task: **Database: Migrate and Seed**.

Without the Dev Container you need Docker, Python 3.12 with
`pip install -r app/requirements.txt`, and Node with pnpm. The script then starts
MariaDB from `.devcontainer/docker-compose.yml` and connects to `127.0.0.1:3306`.

## Run

```bash
bash dev-start.sh
```

or open `repaircafe.code-workspace` and run **Tasks: Run Build Task**
(`Ctrl+Shift+B` → **Full Stack: Start All**).

The script starts (or reuses) the MariaDB container, waits for it, creates the
database if needed, applies pending migrations, and starts:

| Service | URL |
|---|---|
| Frontend (Vite, hot reload) | http://localhost:5173 — use this one |
| Backend (Flask, debug + reload) | http://localhost:5000 |
| Swagger UI | http://localhost:5000/apidocs/ |
| Adminer (database UI) | http://localhost:8089 |

Vite proxies `/api` to Flask. `Ctrl+C` stops both servers; the database keeps running
with its data. `bash dev-start.sh --database-only` starts only the database.

Log in with the seed users:

| User | Password | Role |
|---|---|---|
| `admin` | `admin123` | admin |
| `hans.mueller` | `test123` | helper |
| `erika.schmidt` | `test123` | helper |

The seed also creates six customers, six repairs in all statuses, log entries and a
VDE test.

### Script details

- Defaults: `MYSQL_DATABASE=repaircafepage_dev`, user `root` / `mariadb`, a local-only
  `FLASK_SECRET_KEY`, `LABEL_PRINTER_ENABLED=true`. Values already in the environment
  win.
- Outside the Dev Container the Compose project defaults to
  `<repository-directory>_devcontainer`; override with `DEV_COMPOSE_PROJECT`.
- If either server exits, the other one is stopped. Vite fails instead of switching
  ports when 5173 is taken.
- **Never point the script at a production database.**

If startup reports `Can't locate revision identified by ...`, the database was migrated
by another checkout with different migrations. Use that checkout, or pick another
database with `MYSQL_DATABASE=...` (the script creates it). Don't rewrite Alembic's
history to get past it.

Running Python commands directly (outside the script) needs the environment set
explicitly, because the application default database is `repaircafepage`:

```bash
cd app
export MYSQL_DATABASE=repaircafepage_dev FLASK_ENV=development
python run_migrations.py
python seed_dev.py            # --reset deletes the development data first
```

## Backend

```
app/
├── __init__.py        app factory: config, extensions, blueprints, auth guard, admin bootstrap
├── run.py             creates the app (entry for flask run); optional scheduler
├── config.py          configuration from environment variables
├── extensions.py      db, login manager, CORS, Swagger (registers schema definitions)
├── models.py          SQLAlchemy models
├── schemas.py         Pydantic request/response schemas
├── validation.py      @validate_request decorator
├── utils.py           Pydantic → Swagger conversion, helpers
├── api/               JSON API blueprints (repairs, logs, attachments, VDE tests,
│                      customers, users, settings, config, health)
├── auth/              login, OIDC, PIN session routes, decorators, CSRF check
├── web/routes.py      statistics, XLSX export, e-mail export
├── services/          PDFs, VDE protocol, labels, e-mail, export, PINs, rate limits
├── tasks/             APScheduler job (e-mail export)
├── imports/           PDF signer, Loki logger
├── migrations/        Alembic environment and versions/
├── tests/             pytest suite
├── seed_dev.py        development test data
└── reset_admin_password.py
```

### Tests

```bash
python -m pytest app/tests -v
```

The suite runs on in-memory SQLite and needs no database. `test_api_contract.py`
checks real responses against the OpenAPI schemas.

PIN migration and concurrency checks against MariaDB are opt-in. They need a
disposable database whose name is `pin_tests`, and they create and drop the `users`
and `pin_state` tables:

```bash
PIN_TEST_DATABASE_URL=mysql+pymysql://user:password@host/pin_tests \
  python -m pytest app/tests/test_pins.py -v
```

Never point them at real data, and don't run two of these test processes against the
same database at once.

### Migrations

Migrations live in `app/migrations/versions/` as `NNN_description.py` with
`revision = "NNN"` and `down_revision` set to the previous head (gaps in the numbers
are fine). They read the database from the `MYSQL_*` variables and do not need a
running app.

```bash
cd app && python run_migrations.py                                 # upgrade to head
cd app/migrations && alembic -c alembic.ini upgrade head           # same, via Alembic
```

To add one: copy the latest file, take the next number, set `down_revision` to the
current head, implement `upgrade()` and `downgrade()`. Production applies migrations on
every backend start, so they must be safe to run against existing data.

### Adding or changing an endpoint

1. Pydantic schemas in `app/schemas.py`; register new ones in `init_swagger()` in
   `app/extensions.py`.
2. The route in a blueprint under `app/api/`. Validate the body with
   `@validate_request(Schema)`, protect admin routes with `@admin_required`. Everything
   under `/api` requires login unless marked `@public_endpoint`.
3. Document it in the docstring (Swagger 2.0 YAML after `---`) with an `operationId`,
   and `$ref: '#/definitions/...'` for bodies and responses.
4. Regenerate the spec and the frontend client (see [API.md](API.md#generated-client)).
5. Add tests in `app/tests/`.

## Frontend

```bash
cd frontend
pnpm dev           # Vite dev server on 5173 (dev-start.sh runs this)
pnpm build         # production build → frontend/dist/
pnpm type-check    # vue-tsc
pnpm lint          # eslint --fix
pnpm format        # prettier
pnpm generate-api  # regenerate src/api/generated/ from openapi.json
```

```
frontend/src/
├── api/           client.ts (the generated client + session handling), generated/, documents.ts
├── components/    feature components (dialogs, cards, timeline, …)
│   └── ui/        shared building blocks from the style guide (StatusChip, PersonLabel, …)
├── composables/   useRepairDetail, usePinSession, useCameraStream, useToast, …
├── domain/        repair status rules and categories
├── plugins/       Vuetify theme
├── router/        routes and the login / PIN-lock guard
├── stores/        Pinia: auth, repairs, users
├── styles/        global CSS
├── utils/         dates, names, errors, files
└── views/         pages
```

Conventions:

- `<script setup lang="ts">`, Composition API, strict TypeScript.
- Every API call goes through `api` from `@/api/client` — see
  [`frontend/src/api/API_TYPES.md`](../frontend/src/api/API_TYPES.md).
- UI follows [STYLEGUIDE.md](STYLEGUIDE.md) and uses the components in
  `components/ui/`. ESLint enforces part of it. Admins can see all building blocks at
  `/styleguide`.
- Repair state shared between pages lives in the repair store
  ([`stores/README.md`](../frontend/src/stores/README.md)).

## CI

Every push to `main` and every pull request runs (`.github/workflows/ci.yml`):

| Job | Checks |
|---|---|
| backend | `pytest app/tests`; `frontend/openapi.json` matches `scripts/dump_openapi_spec.py` |
| frontend | `src/api/generated` matches `pnpm generate-api`; `pnpm type-check`; eslint; `pnpm build` |
| audit-backend / audit-frontend | `pip-audit`, `pnpm audit --prod` for known vulnerabilities |

Before pushing:

```bash
python -m pytest app/tests
python scripts/dump_openapi_spec.py && (cd frontend && pnpm generate-api)
(cd frontend && pnpm type-check && pnpm exec eslint src --quiet)
```

## Releases

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `chore:`, …). On `main`, Release Please keeps a release PR open that
bumps `VERSION`, `frontend/package.json` and `CHANGELOG.md`. Merging it tags the
release and publishes multi-arch images to GHCR as `:<version>` and `:latest`. Every
push to `main` also publishes `:dev` images. Dependabot opens dependency updates.

## AI assistant context

`.github/instructions/` holds Copilot instructions for recurring tasks (new API
endpoint, app config value, settings dropdowns, linked settings fields).
`.agents/skills/` holds Vue best-practice skills used for frontend reviews.

## Troubleshooting

| Problem | Fix |
|---|---|
| Database not reachable | `docker ps` — is the `db` container of the Dev Container project running? `bash dev-start.sh --database-only` |
| `Can't locate revision …` | see [Script details](#script-details) |
| `Migration error: table already exists` | the database was partly migrated; inspect it in Adminer, or use a fresh `MYSQL_DATABASE` |
| 401 on every API call | log in again at :5173; make sure you use the Vite URL, not :5000 |
| Port 5173 in use | stop the other Vite process (`npx kill-port 5173`) |
| CI: `openapi.json is outdated` | `python scripts/dump_openapi_spec.py`, then `pnpm generate-api`, commit both |
| Frontend type errors after a backend change | regenerate the client, then `pnpm type-check` |
| Missing frontend dependencies | `cd frontend && pnpm install` |
