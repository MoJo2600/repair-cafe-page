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

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Label Printing Flow                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Vue Frontend                                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  RepairsList.vue                                             │  │
│  │  - Print button for each repair                             │  │
│  │  - Calls POST /api/print-label/<id>                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  Flask Backend (in Docker Container)                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  /api/print-label/<id>                                       │  │
│  │  1. Fetch repair data from database                         │  │
│  │  2. Generate QR code (edit URL with token)                  │  │
│  │  3. Create label image (496x232px, 62mm x 29mm @ 203 DPI)   │  │
│  │  4. Convert to ESC/POS commands                             │  │
│  │  5. Send to CUPS server on host                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  Container CUPS Client                                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Environment: CUPS_SERVER=host.docker.internal:631          │  │
│  │  Config: /etc/cups/client.conf                              │  │
│  │  Commands: lpr, lpstat, lpq                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              │ Network (via host.docker.internal)   │
│                              ▼                                       │
└─────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Host Machine                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  CUPS Server (cupsd)                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Listening on: *:631                                         │  │
│  │  Accepts connections from: 172.16.0.0/12 (Docker network)   │  │
│  │  Manages printer queues                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  Printer Queue: SLP650                                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Device: /dev/usb/lp0 or usb://...                          │  │
│  │  Driver: Generic ESC/POS or SLP650 specific                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  SLP 650 Label Printer (USB connected)                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Label Size: 62mm x 29mm                                     │  │
│  │  Resolution: 203 DPI                                         │  │
│  │  Interface: USB                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Host CUPS Configuration

The container uses the host's CUPS server for printing. This requires proper CUPS configuration on the host machine.

#### Step 1: Edit CUPS Configuration

```bash
# Edit the main CUPS configuration file
sudo nano /etc/cups/cupsd.conf
```

Add or modify these sections:

```apache
# Listen on all interfaces (allow network connections)
Listen *:631

# Allow access from Docker containers
<Location />
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 172.16.0.0/12      # Docker default network range
  Allow from host.docker.internal
</Location>

<Location /admin>
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 172.16.0.0/12
</Location>

<Location /admin/conf>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 172.16.0.0/12
</Location>
```

#### Step 2: Restart CUPS

```bash
sudo systemctl restart cups
```

#### Step 3: Verify CUPS is Listening

```bash
# Check if CUPS is listening on port 631
sudo netstat -tlnp | grep 631

# Or using ss command
sudo ss -tlnp | grep 631

# Expected output:
# tcp   0   0 0.0.0.0:631   0.0.0.0:*   LISTEN   1234/cupsd
```

#### Step 4: Configure SLP 650 Printer in CUPS

```bash
# List available USB printers
lpinfo -v

# Add the SLP 650 printer
lpadmin -p SLP650 -v usb://... -E -m drv:///sample.drv/generic-escp.ppd

# Or use the CUPS web interface
# Navigate to: http://localhost:631
# Administration > Add Printer > Select SLP 650
```

### Container Configuration

The dev container is configured to communicate with the host CUPS server:

**Dockerfile:**
- Installs only `cups-client` (not full CUPS server)
- Creates `/etc/cups/client.conf` pointing to `host.docker.internal:631`

**docker-compose.yml:**
- Sets `CUPS_SERVER=host.docker.internal:631` environment variable
- No USB device access required — the container talks to the host CUPS server over the network

### Label Content

Each printed label includes:
- **Repair ID** (large, bold at top)
- **Date** of repair
- **Customer name** (first + last)
- **Repair type** (category)
- **Device type**
- **Status** (Open/Closed) with color indicator
- **QR Code** (180x180px on right side)
  - Contains URL: `http://repaircafe/edit/{id}/{qr_token}`
  - Scannable with camera to access repair details

### Print Method

The label service prints via CUPS using the `lp` command. The container connects to the CUPS server running on the Docker host.

```
POST /api/print-label/123  →  lp -d <LABEL_PRINTER_NAME>  →  host CUPS  →  printer
```

### Environment Variables

Set these in your `.env` or `docker-compose.yml`:

```bash
# Enable the print button and endpoint
LABEL_PRINTER_ENABLED=true

# Name of the printer queue in host CUPS (must match exactly)
LABEL_PRINTER_NAME=SLP650
```

For network printing (printer connected to another machine on the LAN), configure the host CUPS server to forward jobs to the remote printer. See `docs/CUPS_NETWORK_SETUP.md` for step-by-step instructions.

### Troubleshooting

**Check CUPS connection from container:**
```bash
# Inside container
lpstat -r
# Should show: scheduler is running

lpstat -p -d
# Should list available printers including SLP650
```

**Test print from container:**
```bash
# Inside container
echo "Test print" | lpr -P SLP650
```

**Check CUPS logs on host:**
```bash
# On host machine
sudo tail -f /var/log/cups/error_log
```

**Permission issues:**
```bash
# On host, add your user to lpadmin group
sudo usermod -a -G lpadmin $USER

# Restart CUPS
sudo systemctl restart cups
```

