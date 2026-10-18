# RepairCafe Development Documentation

## Getting Started

The project runs inside a Dev Container (MariaDB + Python + Node). Initialize
the separate development database once, from the repository root:

```bash
bash dev-start.sh --setup
```

This creates `repaircafepage_dev` if needed, runs migrations, and seeds test
data. It never drops a database or resets existing data. Re-running it skips
seeding if the test users already exist. In VS Code the equivalent task is
**Database: Migrate and Seed**.

Open
`repaircafe.code-workspace` and run **Tasks: Run Build Task** (`Ctrl+Shift+B`)
to start **Full Stack: Start All**. Alternatively, from the repository root:

```bash
bash dev-start.sh
```

Startup reuses the Dev Container's MariaDB container (or creates it if missing),
waits up to 120 seconds for database readiness, ensures `repaircafepage_dev`
exists, applies pending migrations, and
starts Flask with debug/reload on port 5000 and Vite with hot reload on port 5173.
If either server exits, the other is stopped too. Vite fails if port 5173 is
already occupied rather than silently switching ports.

Press `Ctrl+C` in the task terminal, or use **Tasks: Terminate Task**, to stop
both servers. MariaDB is left running and its data is preserved. To start just
the database, use **Database: Start** or `bash dev-start.sh --database-only`.

Python dependencies must be installed first (the Dev Container normally does
this automatically). Missing frontend dependencies are installed by the script:

```bash
pip install --user -r app/requirements.txt
```

Development test data is never seeded or reset during normal startup. Run setup
explicitly when initializing a new development database:

```bash
bash dev-start.sh --setup
```

The script detects the current Dev Container's Compose project. Outside the
Dev Container it defaults to `<repository-directory>_devcontainer` and connects
to MariaDB on `127.0.0.1:3306`. Use `DEV_COMPOSE_PROJECT` to select a different
development Compose project. Existing `MYSQL_*` environment values are preserved.
The development default is `repaircafepage_dev`; the original `repaircafepage`
database is left untouched. Workspace tasks, the development debugger, and the
SQLTools connection also use `repaircafepage_dev`. Do not point this script at production.
It supplies a local-only session secret unless `FLASK_SECRET_KEY` is already set.

If startup reports `Can't locate revision identified by ...`, the selected
database was migrated by a different checkout. Use the checkout with the matching
migrations, or select a separate development database with `MYSQL_DATABASE`
(the script creates it if missing). Startup intentionally stops instead of resetting
data or rewriting Alembic's revision history.

| Service         | URL                   |
| --------------- | --------------------- |
| Frontend (Vite) | http://localhost:5173 |
| Backend (Flask) | http://localhost:5000 |
| Adminer (DB UI) | http://localhost:8089 |

---

## Database

### Connection

The app uses SQLAlchemy + PyMySQL. Connection is configured via environment
variables. The development startup script uses these defaults; direct Python
commands must set `MYSQL_DATABASE=repaircafepage_dev` explicitly because the
application's fallback remains `repaircafepage`:

| Variable           | Default                             | Description          |
| ------------------ | ----------------------------------- | -------------------- |
| `MYSQL_HOST`       | `db`                                | MariaDB host         |
| `MYSQL_DATABASE`   | `repaircafepage_dev`                | Development database |
| `MYSQL_USER`       | `root`                              | Username             |
| `MYSQL_PASSWORD`   | `mariadb`                           | Password             |
| `FLASK_SECRET_KEY` | `repaircafe-local-development-only` | Local session secret |

### Migrations

Migrations live in `app/migrations/versions/` and follow Alembic's revision
chain. Each file sets `revision = "NNN"` and `down_revision` to the previous
revision (or `None` for the initial migration).

Migrations do **not** require a running Flask application. The database URL is
read directly from the `MYSQL_*` environment variables.

**Apply all pending migrations:**

```bash
cd /workspaces/repaircafepage/app
MYSQL_DATABASE=repaircafepage_dev python run_migrations.py
```

**Or using Alembic directly** (same env vars must be set):

```bash
cd /workspaces/repaircafepage/app/migrations
MYSQL_DATABASE=repaircafepage_dev alembic -c alembic.ini upgrade head
```

**Adding a new migration:**

Create a new file in `app/migrations/versions/` following the naming
convention `NNN_description.py`. Set `revision` to the next number and
`down_revision` to the current head. Implement `upgrade()` and `downgrade()`.

### Development Seed Data

After running migrations you can populate the database with realistic test data:

```bash
cd /workspaces/repaircafepage/app
MYSQL_DATABASE=repaircafepage_dev FLASK_ENV=development python seed_dev.py          # skips if data already exists
MYSQL_DATABASE=repaircafepage_dev FLASK_ENV=development python seed_dev.py --reset  # deletes development data before seeding
```

**What gets seeded:**

| Resource        | Details                                                                           |
| --------------- | --------------------------------------------------------------------------------- |
| **Users**       | `admin / admin123` (admin), `hans.mueller / test123`, `erika.schmidt / test123`   |
| **Customers**   | Kurt Wagner, Maria Hoffmann, Peter Klein, Sabine Braun, Georg Fischer, Lisa Weber |
| **Repairs**     | 6 repairs across all statuses: Offen, In Arbeit, Repariert, Nicht reparierbar     |
| **Repair logs** | 5 log entries spread across repairs                                               |
| **VDE test**    | 1 passing test on a Wasserkocher (Schutzklasse I, all checks passed)              |

---

## Models

All models are defined in `app/models.py`.

### User

Repair volunteers and admins. Used for Flask-Login sessions.

| Column                 | Type        | Notes                  |
| ---------------------- | ----------- | ---------------------- |
| `id`                   | Integer PK  |                        |
| `username`             | String(100) | unique                 |
| `vorname` / `nachname` | String(100) |                        |
| `email`                | String(100) | unique                 |
| `password_hash`        | String(255) | Werkzeug pbkdf2        |
| `is_admin`             | Boolean     | grants admin access    |
| `is_active`            | Boolean     | disabling blocks login |
| `created_at`           | DateTime    |                        |

### Setting

Configurable dropdown values (repair types, test devices). Replaces the old
`dropdown_data.yaml`.

| Column          | Type        | Notes                                      |
| --------------- | ----------- | ------------------------------------------ |
| `id`            | Integer PK  |                                            |
| `category`      | String(50)  | indexed; e.g. `repair_type`, `test_device` |
| `name`          | String(200) | unique within category                     |
| `serial_number` | String(100) | optional; used for `test_device`           |
| `sort_order`    | Integer     | display order                              |
| `is_active`     | Boolean     | hide without deleting                      |

### Customer

Reusable contact record that can be linked to multiple repairs.

### Repair

Core record. Notable fields:

| Column        | Type           | Notes                                                     |
| ------------- | -------------- | --------------------------------------------------------- |
| `customer_id` | FK → customers | optional link                                             |
| `user_id`     | FK → users     | assigned repairer                                         |
| `status`      | String(20)     | `Offen` / `In Arbeit` / `Repariert` / `Nicht reparierbar` |
| `qr_token`    | String(32)     | unique hex token for QR code / public link                |
| `din_pruef`   | Boolean        | flags that a VDE test is required                         |

### RepairLog

One entry per work session on a repair. Replaces the single
`reparatur_besch` / `reparatur_dauer` fields on `Repair`.

### VdeTest

Electrical safety test result (DIN VDE 0701/0702) linked to a repair.
Records Sichtpruefung, Schutzleiterwiderstand, Isolationswiderstand,
Ableitstrom, and Gesamtergebnis.

---

## API

All API routes are prefixed with `/api`. Authentication uses HTTP-only
session cookies (Flask-Login). Most write endpoints require login;
`@admin_required` guards admin-only endpoints.

### Auth

| Method | Path               | Notes                        |
| ------ | ------------------ | ---------------------------- |
| POST   | `/api/auth/login`  | body: `{username, password}` |
| GET    | `/api/auth/me`     | returns current user         |
| POST   | `/api/auth/logout` |                              |

### Repairs

| Method | Path                            | Auth  | Notes                   |
| ------ | ------------------------------- | ----- | ----------------------- |
| GET    | `/api/list`                     | —     | list all repairs        |
| POST   | `/api/repairs`                  | login | create repair           |
| PUT    | `/api/repairs/<id>`             | login | update repair           |
| DELETE | `/api/repairs/<id>`             | admin | delete repair           |
| GET    | `/api/repairs/by-token/<token>` | —     | public QR lookup        |
| POST   | `/api/repairs/<id>/disclaimer`  | —     | save signature          |
| GET    | `/api/repairs/<id>/disclaimer`  | login | download disclaimer PDF |

### Repair Logs

| Method | Path                                    | Auth  |
| ------ | --------------------------------------- | ----- |
| GET    | `/api/repairs/<id>/logs`                | login |
| POST   | `/api/repairs/<id>/logs`                | login |
| GET    | `/api/repairs/<id>/logs/<log_id>`       | login |
| PUT    | `/api/repairs/<id>/logs/<log_id>`       | login |
| POST   | `/api/repair_logs/<log_id>/attachments` | login |
| GET    | `/api/repairs/<id>/log_attachments`     | login |

### VDE Tests

| Method | Path                                        | Auth  | Notes                       |
| ------ | ------------------------------------------- | ----- | --------------------------- |
| GET    | `/api/repairs/<id>/vde-tests`               | —     | list tests                  |
| POST   | `/api/repairs/<id>/vde-tests`               | login | create test                 |
| GET    | `/api/repairs/<id>/vde-tests/<test_id>`     | login | single test                 |
| GET    | `/api/repairs/<id>/vde-tests/<test_id>/pdf` | login | download Pruefprotokoll PDF |

### Users

| Method | Path              | Auth  |
| ------ | ----------------- | ----- |
| GET    | `/api/users`      | login |
| GET    | `/api/users/<id>` | login |
| POST   | `/api/users`      | admin |
| PUT    | `/api/users/<id>` | admin |
| DELETE | `/api/users/<id>` | admin |

### Settings

| Method | Path                 | Auth  |
| ------ | -------------------- | ----- |
| GET    | `/api/settings`      | login |
| GET    | `/api/settings/all`  | login |
| POST   | `/api/settings`      | admin |
| PUT    | `/api/settings/<id>` | admin |
| DELETE | `/api/settings/<id>` | admin |

### Customers

| Method | Path                    | Auth  |
| ------ | ----------------------- | ----- |
| GET    | `/api/customers`        | login |
| GET    | `/api/customers/search` | login |
| POST   | `/api/customers`        | login |
| GET    | `/api/customers/<id>`   | login |
| PUT    | `/api/customers/<id>`   | login |
| DELETE | `/api/customers/<id>`   | admin |

---

## Frontend

Built with **Vue 3 + TypeScript + Vuetify 3 + Pinia**. Source is in
`frontend/src/`.

```
frontend/src/
  api/           generated client types + hand-written service wrappers
  components/    reusable Vue components
  composables/   shared logic (useRepairThread, etc.)
  plugins/       Vuetify, router setup
  router/        vue-router routes
  stores/        Pinia stores
  views/         page-level components
```

All authenticated API calls use `fetch(url, { credentials: "include" })` to
send the session cookie. The generated `OpenAPI.ts` client is **not** used for
authenticated requests.

**Type-check:**

```bash
cd frontend && pnpm type-check
```

---

## Troubleshooting

### Database not reachable

- Ensure the `db` container is running: `docker compose ps`
- Check credentials match `docker-compose.yml`

### Migration error: table already exists

- The database may have been partially migrated. Check with Adminer at
  http://localhost:8089, then drop and recreate if needed.

### 401 on API requests

- The session cookie is not being sent. Ensure `credentials: "include"` is set
  in the `fetch` call. The generated `__request` client does not include
  credentials by default.

### Frontend build errors

- Run `pnpm install` inside `frontend/` to ensure dependencies are up to date.
- Run `pnpm type-check` to surface TypeScript errors before building.

---

```
    /\_/\
   ( o.o )
    > ^ <
   /|   |\
  (_|   |_)
```
