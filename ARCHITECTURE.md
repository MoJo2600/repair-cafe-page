# Architecture Diagram

## Development Mode Setup

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Your Computer                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Terminal 1                          Terminal 2                      │
│  ┌──────────────────────┐           ┌──────────────────────┐        │
│  │  npm run dev         │           │  python api.py       │        │
│  │                      │           │                      │        │
│  │  Vite Dev Server     │           │  Flask Backend       │        │
│  │  Port: 5173          │◄─────────►│  Port: 5000/8088     │        │
│  │                      │  Proxies  │                      │        │
│  │  - Hot Reload        │  /api/*   │  - API endpoints     │        │
│  │  - Vue Components    │           │  - Authentication    │        │
│  │  - TypeScript        │           │  - Database          │        │
│  │  - Vuetify UI        │           │  - Business Logic    │        │
│  └──────────────────────┘           └──────────────────────┘        │
│           │                                   │                      │
│           │                                   │                      │
│           ▼                                   ▼                      │
│  ┌──────────────────────┐           ┌──────────────────────┐        │
│  │ Browser              │           │ Browser              │        │
│  │ http://localhost:5173│           │ http://localhost:8088│        │
│  │                      │           │ /vue or /index       │        │
│  │ ← USE THIS FOR DEV   │           │                      │        │
│  └──────────────────────┘           └──────────────────────┘        │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

How it works:
1. You access http://localhost:5173 (Vite)
2. Vue app loads with instant hot reload
3. When you call /api/*, Vite proxies to Flask at port 5000/8088
4. Flask handles the API request and returns data
5. Vue updates the UI
```

## Production Mode Setup

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Production Server                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Step 1: Build Frontend (one time)                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  $ npm run build                                             │  │
│  │                                                              │  │
│  │  Creates: app/static/dist/                                  │  │
│  │  - assets/main-xxx.js   (Vue app bundle)                    │  │
│  │  - assets/main-xxx.css  (Vuetify styles)                    │  │
│  │  - assets/*.woff2       (Material Design Icons)             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Step 2: Run Flask                                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  $ python api.py --config prod                               │  │
│  │                                                              │  │
│  │  Flask Server (Port 80 or 5000)                             │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │                                                          │ │  │
│  │  │  Routes:                                                 │ │  │
│  │  │  ┌──────────────────────────────────────────────────┐  │ │  │
│  │  │  │ /vue          → Serves vue_app.html             │  │ │  │
│  │  │  │                 (loads app/static/dist/*)       │  │ │  │
│  │  │  ├──────────────────────────────────────────────────┤  │ │  │
│  │  │  │ /api/*        → API endpoints                   │  │ │  │
│  │  │  ├──────────────────────────────────────────────────┤  │ │  │
│  │  │  │ /index        → Existing Flask templates        │  │ │  │
│  │  │  │ /list, /edit  → Existing pages                  │  │ │  │
│  │  │  └──────────────────────────────────────────────────┘  │ │  │
│  │  │                                                          │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│                    ┌──────────────────────┐                         │
│                    │ Browser              │                         │
│                    │ http://your-server   │                         │
│                    │ /vue                 │                         │
│                    └──────────────────────┘                         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

How it works:
1. User visits http://your-server/vue
2. Flask serves vue_app.html template
3. Template loads pre-built JS/CSS from app/static/dist/
4. Vue app initializes in browser
5. API calls go to /api/* routes on same server
6. Flask handles API requests and returns data
```

## File Flow

```
Development:
  frontend/src/App.vue
  frontend/src/components/HelloWorld.vue
       ↓ (Vite processes)
  Browser (http://localhost:5173)

Production:
  frontend/src/App.vue
  frontend/src/components/HelloWorld.vue
       ↓ (npm run build)
  app/static/dist/assets/main-xxx.js
  app/static/dist/assets/main-xxx.css
       ↓ (Flask serves)
  app/templates/vue_app.html
       ↓
  Browser (http://your-server/vue)
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (Vue.js)              Backend (Flask)              │
│  ┌───────────────────────┐     ┌───────────────────────┐   │
│  │ Components:           │     │ Existing Routes:      │   │
│  │ - HelloWorld.vue      │     │ - /index             │   │
│  │ - ApiExample.vue      │     │ - /list              │   │
│  │ - Your components...  │     │ - /edit/<id>         │   │
│  │                       │     │ - /login             │   │
│  ├───────────────────────┤     ├───────────────────────┤   │
│  │ Makes API calls to:   │     │ API Routes:           │   │
│  │ - /api/logEvent       │◄────┤ - /api/logEvent      │   │
│  │ - /api/dump/repair    │◄────┤ - /api/dump/repair   │   │
│  │ - /api/mailexport     │◄────┤ - /api/mailexport    │   │
│  │ - /add                │◄────┤ - /add               │   │
│  │ - /alterRepair/<id>   │◄────┤ - /alterRepair/<id>  │   │
│  │ - /stat-data/<type>   │◄────┤ - /stat-data/<type>  │   │
│  └───────────────────────┘     └───────────────────────┘   │
│                                                               │
│  You can:                                                    │
│  1. Keep existing Flask templates (/index, /list, /edit)    │
│  2. Gradually migrate to Vue components                      │
│  3. Or build new features entirely in Vue                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
┌────────────────────────────────────────────────────────────┐
│  Vue App tries to access /vue route                        │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────┐                 │
│  │ Flask @flask_login.login_required    │                 │
│  └──────────────────────────────────────┘                 │
│         │                                                   │
│         ├─ Not logged in ──► Redirect to /login           │
│         │                                                   │
│         └─ Logged in ─────► Serve Vue app                 │
│                                                             │
│  Vue app makes API call to /api/*                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────┐                 │
│  │ Flask checks session                 │                 │
│  └──────────────────────────────────────┘                 │
│         │                                                   │
│         ├─ Not logged in ──► Return 401/redirect          │
│         │                                                   │
│         └─ Logged in ─────► Process request & return data │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

This keeps your existing authentication system intact!

## Label Printing System

### Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        Label Printing Flow                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Vue Frontend                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  RepairsList.vue / EditRepair.vue                            │   │
│  │  - Print button shown when LABEL_PRINTER_ENABLED=true        │   │
│  │  - Calls POST /api/print-label/<id>                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  Flask Backend (in Docker Container)                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  /api/print-label/<id> -> LabelService.print_label()         │   │
│  │  1. Fetch repair data & app_cfg (app_url, org_name, website) │   │
│  │  2. Generate QR code (<app_url>/edit/<qr_token>)             │   │
│  │  3. Render PNG image (602x330px, 51mm x 28mm @ 300 DPI)      │   │
│  │  4. Invoke: lp -d <LABEL_PRINTER_NAME> <tmp.png>             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  Container CUPS Client                                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Package: cups-client                                        │   │
│  │  Config: /etc/cups/client.conf (ServerName /run/cups/cups.sock)│ │
│  │  Commands: lp, lpstat                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              │ Mounted Unix Socket                  │
│                              │ (/run/cups/cups.sock)                │
│                              ▼                                      │
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Host Machine                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CUPS Server (cupsd)                                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Listening on: /run/cups/cups.sock                           │   │
│  │  Queue: SLP650                                               │   │
│  │  - Option A (Local USB): usb://SII/SLP650?serial=...         │   │
│  │    Filter: seikoslp.rastertolabel (siislp650.ppd.gz)         │   │
│  │  - Option B (Remote Print Server):                           │   │
│  │    ipp://<printserver>:631/printers/SII_SLP650 (everywhere)  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  SII SLP 650 Label Printer                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Label Size: 51mm x 28mm (MultiPurpose)                      │   │
│  │  Resolution: 300 DPI (602 x 330 px)                          │   │
│  │  Interface: USB (local to Docker host or on remote Pi)       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Docker & DevContainer Configuration

Both production (`compose.yaml` + `Dockerfile.backend`) and development (`.devcontainer/docker-compose.yml` + `.devcontainer/Dockerfile`) use the host's CUPS Unix socket rather than exposing TCP port 631 to the container network:

1. **`Dockerfile.backend` / `.devcontainer/Dockerfile`**:
   - Installs `cups-client` and `fonts-dejavu-core`.
   - Writes `ServerName /run/cups/cups.sock` to `/etc/cups/client.conf`.
2. **`compose.yaml` / `.devcontainer/docker-compose.yml`**:
   - Mounts `/run/cups/cups.sock:/run/cups/cups.sock` into the container.
   - Passes `LABEL_PRINTER_ENABLED` and `LABEL_PRINTER_NAME` into the container environment.

```yaml
services:
  backend:
    environment:
      LABEL_PRINTER_ENABLED: ${LABEL_PRINTER_ENABLED:-false}
      LABEL_PRINTER_NAME: ${LABEL_PRINTER_NAME:-SLP650}
    volumes:
      - app_data:/data
      - ./config:/config:ro
      - /run/cups/cups.sock:/run/cups/cups.sock
```

### Label Content

Each printed label (`602 × 330` px PNG generated by `app/services/label_service.py`) includes:
- **Date** of repair (top left)
- **Customer name** (`vorname` + `nachname`, up to 3 wrapped lines)
- **Device type** (`geraet_art`)
- **QR Code** (`207 × 207` px on the right side, linking to `<app_url>/edit/<qr_token>`)
- **Repair ID** (`#123`, centered below the QR code)
- **Logo, Organisation Name & Website** (bottom left; uses `/data/logo.png` if present, otherwise `app/static/logo.jpg`)

### Print Method & Environment Variables

```text
POST /api/print-label/123  →  lp -d <LABEL_PRINTER_NAME> <tmp.png>  →  /run/cups/cups.sock  →  host CUPS  →  printer
```

Set these in your `.env`:

```bash
# Enable the print button in the UI and the /api/print-label/<id> endpoint
LABEL_PRINTER_ENABLED=true

# Exact name of the printer queue on the Docker host CUPS server
LABEL_PRINTER_NAME=SLP650
```

For full step-by-step instructions covering **Docker configuration**, **local USB setup**, and **remote print server (Raspberry Pi) setup**, see [`docs/CUPS_NETWORK_SETUP.md`](docs/CUPS_NETWORK_SETUP.md).

### Troubleshooting

**Check CUPS connection from inside the container:**
```bash
docker compose exec backend lpstat -r
# Should show: scheduler is running

docker compose exec backend lpstat -p -d
# Should list available printers including SLP650
```

**Test print a label image from the host or container:**
```bash
lp -d SLP650 test_label.png
```

**Check CUPS logs on host (or remote print server):**
```bash
sudo tail -f /var/log/cups/error_log
```


