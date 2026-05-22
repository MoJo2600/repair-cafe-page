# Quick Reference

## Get Started

### 1. Install Dependencies (First Time Only)

```bash
# Frontend
cd frontend && pnpm install

# Backend
pip install -r app/requirements.txt
```

### 2. Start Development Servers

**Option A — startup script:**
```bash
./dev-start.sh
```

**Option B — two terminals:**

```bash
# Terminal 1 – Frontend
cd frontend && pnpm dev
```

```bash
# Terminal 2 – Backend
cd app && flask run --host 0.0.0.0 --port 5000
```

> Set `FLASK_APP=run.py` and `FLASK_DEBUG=1` before starting Flask, or use the VS Code task **"Full Stack: Start All"**.

### 3. Access the App

| Service | URL |
|---------|-----|
| Vue frontend (dev) | http://localhost:5173 |
| Flask backend | http://localhost:5000 |

---

## Frontend

### Commands

```bash
cd frontend
pnpm dev          # Vite dev server with HMR (port 5173)
pnpm build        # Production build → app/static/dist/
pnpm preview      # Preview production build
pnpm type-check   # TypeScript type check (vue-tsc)
```

### Project Structure

```
frontend/src/
├── api/              # Generated OpenAPI client + services
│   └── services/     # Typed wrappers: RepairsService, CustomersService, …
├── components/       # Reusable Vue components
├── views/            # Page components
├── stores/           # Pinia stores
├── router/           # vue-router config
├── plugins/          # vuetify.ts, etc.
├── App.vue           # Root component
└── main.ts           # Entry point
```

### Key Libraries

- **Vue 3** + Composition API + TypeScript
- **Vuetify 3** — all UI components (`v-btn`, `v-card`, `v-data-table`, …)
- **Pinia** — state management
- **vue-router** — client-side routing
- **OpenAPI client** — generated from backend schema, lives in `frontend/src/api/`

### Useful Docs

- Vuetify components: https://vuetifyjs.com/components/
- Vue 3: https://vuejs.org/
- TypeScript + Vue: https://vuejs.org/guide/typescript/overview.html

---

## Backend

### Commands

```bash
cd app

# Start dev server
flask run --host 0.0.0.0 --port 5000

# Run database migrations
python run_migrations.py
```

### Project Structure

```
app/
├── run.py              # Flask app entry point
├── __init__.py         # App factory (create_app)
├── models.py           # SQLAlchemy ORM models
├── schemas.py          # Pydantic v2 request/response schemas
├── config.py           # Config (DB URL, paths, …)
├── extensions.py       # db, mail, scheduler singletons
├── api/                # API blueprints
│   ├── repairs.py      # /api/repairs
│   ├── repair_logs.py  # /api/repairs/<id>/logs + attachments
│   ├── customers.py    # /api/customers
│   ├── config.py       # /api/config (dropdown data)
│   └── health.py       # /api/health
├── services/           # Business logic (PDF, email, export)
├── migrations/         # Alembic-style migration scripts
│   └── versions/       # 000_… through 014_… (current head)
└── requirements.txt
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_APP` | `run.py` | Flask entry point |
| `FLASK_ENV` | `development` | Environment |
| `FLASK_DEBUG` | `1` | Enable debug mode |
| `DATABASE_URL` | set in config.py | MySQL connection string |

### Database Migrations

Migrations do **not** need a running Flask app — the DB URL comes from env vars.

```bash
cd app && python run_migrations.py
```

The initial admin user is created **automatically on first app startup**.

---

## Production Build

```bash
# 1. Build frontend (output goes to app/static/dist/)
cd frontend && pnpm build

# 2. Start Flask (serves the built assets)
cd app && flask run --host 0.0.0.0 --port 5000
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 5173 in use | `npx kill-port 5173` |
| TypeScript errors | `cd frontend && pnpm type-check` |
| Clean frontend install | `rm -rf frontend/node_modules && cd frontend && pnpm install` |
| Python import error | `pip install -r app/requirements.txt` |
| DB schema out of date | `cd app && python run_migrations.py` |

---

## Further Reading

- **Architecture**: `ARCHITECTURE.md`
- **Full deployment guide**: `DEPLOYMENT.md`
- **Frontend details**: `FRONTEND.md`
- **Pinia migration notes**: `PINIA_MIGRATION.md`
