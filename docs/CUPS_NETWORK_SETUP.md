# Label Printer Setup Guide (Seiko SLP 650 & CUPS)

This guide explains how to set up the **Seiko Instruments Smart Label Printer 650 (SII SLP 650)** for **RepairCafePage**. It covers three core areas plus important operational details and pitfalls:

1. **[Topic A – Accessing the Printer from Docker](#topic-a--accessing-the-printer-from-docker)**: How the backend container communicates with the host's CUPS daemon.
2. **[Topic B – Printer on the Same Machine as the Docker Host](#topic-b--printer-on-the-same-machine-as-the-docker-host-local-usb)**: Direct USB setup on the machine running Docker.
3. **[Topic C – Printer on a Remote Print Server](#topic-c--printer-on-a-remote-machine-raspberry-pi--linux-print-server)**: Connecting a remote USB printer (e.g., on a Raspberry Pi) to the Docker host over IPP/CUPS.
4. **[Important Details & Common Pitfalls](#important-details--common-pitfalls-dont-miss-these)**: Driver forks, filter permissions, `ServerAlias *`, page sizes, QR code URLs, and queue recovery.
5. **[Verification & Troubleshooting](#verification--troubleshooting)**: Layer-by-layer testing and debugging commands.

---

## Architecture Overview

RepairCafePage generates label images in [`app/services/label_service.py`](../app/services/label_service.py) as **602 × 330 px** PNG files (`51 mm × 28 mm` at `300 DPI`) and submits them to CUPS using the standard `lp` command:

```text
POST /api/print-label/<id>  ──►  generate_label_image() (602×330 PNG)  ──►  lp -d <LABEL_PRINTER_NAME> <tmp.png>
```

Depending on where the physical printer is plugged in, the print job follows one of two paths:

### Scenario B: Local USB Printer (Same Machine as Docker Host)

```text
┌──────────────────────────────┐                  ┌──────────────────────────────┐
│  Docker Container (backend)  │                  │  Docker Host (Linux)         │
│                              │  Unix Socket     │                              │
│  lp -d SLP650 <label.png> ───┼─/run/cups/───────►  cupsd (Queue: SLP650)       │
│  (/etc/cups/client.conf)     │  cups.sock       │    │ seikoslp.rastertolabel  │
└──────────────────────────────┘                  └────┼─────────────────────────┘
                                                       │ USB
                                                       ▼
                                                  ┌──────────────┐
                                                  │ SII SLP 650  │
                                                  └──────────────┘
```

### Scenario C: Remote Print Server (e.g., Raspberry Pi on the LAN)

```text
┌──────────────────────────────┐                  ┌──────────────────────────────┐                  ┌──────────────────────────────┐
│  Docker Container (backend)  │                  │  Docker Host (Linux)         │                  │  Remote Print Server (Pi)    │
│                              │  Unix Socket     │                              │  IPP (Port 631)  │                              │
│  lp -d SLP650 <label.png> ───┼─/run/cups/───────►  cupsd (Queue: SLP650)       ┼──ipp://<IP>:631──►  cupsd (Queue: SII_SLP650)   │
│  (/etc/cups/client.conf)     │  cups.sock       │  (IPP Everywhere Relay)      │                  │    │ seikoslp.rastertolabel  │
└──────────────────────────────┘                  └──────────────────────────────┘                  └────┼─────────────────────────┘
                                                                                                         │ USB
                                                                                                         ▼
                                                                                                    ┌──────────────┐
                                                                                                    │ SII SLP 650  │
                                                                                                    └──────────────┘
```

---

## Topic A – Accessing the Printer from Docker

The Docker container does **not** need direct USB passthrough or TCP network port exposure to print. Instead, it communicates with the **Docker host's CUPS daemon** over a mounted Unix domain socket (`/run/cups/cups.sock`). This exact same container configuration works regardless of whether the printer is connected locally via USB to the Docker host ([Topic B](#topic-b--printer-on-the-same-machine-as-the-docker-host-local-usb)) or connected to a remote print server ([Topic C](#topic-c--printer-on-a-remote-machine-raspberry-pi--linux-print-server)).

### 1. Backend Container Image (`Dockerfile.backend`)

In [`Dockerfile.backend`](../Dockerfile.backend), the image is built with the CUPS client tools and pre-configured to use the Unix socket:

```dockerfile
# System packages required by Python deps (PyMuPDF, Pillow), PDF fonts, and CUPS label printing
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core libglib2.0-0 libgl1 cups-client \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /etc/cups && echo "ServerName /run/cups/cups.sock" > /etc/cups/client.conf
```

**Explanation:**
- `cups-client`: Installs the `lp` and `lpstat` CLI binaries invoked by [`app/services/label_service.py`](../app/services/label_service.py). No `cupsd` server daemon runs inside the container.
- `fonts-dejavu-core`: Provides `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` and `DejaVuSans-Bold.ttf` used by Pillow when rendering the `602 × 330` px label PNG.
- `/etc/cups/client.conf` (`ServerName /run/cups/cups.sock`): Directs `lp` and `lpstat` inside the container to talk to `/run/cups/cups.sock` instead of `localhost:631`.

### 2. Production Docker Compose Template (`compose.yaml`)

In [`compose.yaml`](../compose.yaml), the `backend` service passes the printer environment variables and bind-mounts `/run/cups/cups.sock` from the Docker host:

```yaml
services:
  frontend:
    image: ghcr.io/mojo2600/repaircafepage-frontend:latest
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    image: ghcr.io/mojo2600/repaircafepage-backend:latest
    restart: unless-stopped
    environment:
      FLASK_ENV: production
      DATA_DIR: ${DATA_DIR:-/data}
      CONFIG_DIR: ${CONFIG_DIR:-/config}
      MYSQL_HOST: db
      MYSQL_DATABASE: ${MYSQL_DATABASE:-repaircafepage}
      MYSQL_USER: ${MYSQL_USER:-repaircafe}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      FLASK_SECRET_KEY: ${FLASK_SECRET_KEY}
      PUBLIC_URL: ${PUBLIC_URL:-}
      # ── Label Printer Configuration ─────────────────────────────────────────
      # Enables the print button in the UI and POST /api/print-label/<id>
      LABEL_PRINTER_ENABLED: ${LABEL_PRINTER_ENABLED:-false}
      # Must match the exact CUPS queue name on the Docker host (`lpstat -p`)
      LABEL_PRINTER_NAME: ${LABEL_PRINTER_NAME:-SLP650}
    extra_hosts:
      - "host-gateway:host-gateway"
    volumes:
      - app_data:/data
      - ./config:/config:ro
      # ── Host CUPS Unix Socket Mount ─────────────────────────────────────────
      # Gives `lp` inside the container direct access to the host's cupsd socket:
      - /run/cups/cups.sock:/run/cups/cups.sock
    depends_on:
      db:
        condition: service_healthy
```

**Explanation:**
- `- /run/cups/cups.sock:/run/cups/cups.sock`: Bind-mounts the host's active CUPS socket into the container. Because it is a Unix domain socket, **no firewall changes, port mappings, or Docker bridge subnet rules (`Allow from 172.17.0.0/16`) are needed on the Docker host**.
- Make sure the `cups` service is installed and running on the Docker host (`sudo systemctl enable --now cups`) **before** starting the container so that `/run/cups/cups.sock` exists on the host as a socket file (otherwise Docker would create an empty directory at `/run/cups/cups.sock`).

### 3. Environment Configuration (`.env` / `.env.example`)

In your `.env` file (copied from [`.env.example`](../.env.example)), configure:

```dotenv
# Browser-facing URL of the RepairCafePage instance.
# Used as the fallback base URL for the QR code printed on labels (<PUBLIC_URL>/edit/<qr_token>).
PUBLIC_URL=https://repairs.example.org

# -- Label Printer (Optional, CUPS) ------------------------------------------
# Set to true to expose the "Print Label" button in the UI and enable the
# POST /api/print-label/<id> endpoint.
LABEL_PRINTER_ENABLED=true

# Exact CUPS queue name configured on the Docker host (verify with `lpstat -p`).
# - Local USB printer on Docker host: name of the local USB queue (e.g. SLP650).
# - Remote print server (e.g. Raspberry Pi): name of the local IPP Everywhere
#   relay queue on the Docker host (e.g. SLP650 -> ipp://<printserver>:631/printers/SII_SLP650).
LABEL_PRINTER_NAME=SLP650
```

After changing `.env`, always recreate the `backend` container (a simple `docker compose restart` does not reload `.env`):

```bash
docker compose up -d --force-recreate backend
```

### 4. DevContainer Template (`.devcontainer/docker-compose.yml`)

For local development inside VS Code Dev Containers, [`.devcontainer/Dockerfile`](../.devcontainer/Dockerfile) and [`.devcontainer/docker-compose.yml`](../.devcontainer/docker-compose.yml) use the exact same CUPS socket mechanism:

```yaml
services:
  devcontainer:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      LABEL_PRINTER_ENABLED: ${LABEL_PRINTER_ENABLED:-true}
      LABEL_PRINTER_NAME: ${LABEL_PRINTER_NAME:-SLP650}
    volumes:
      - ../..:/workspaces:cached
      - /var/run/docker.sock:/var/run/docker.sock
      - /dev/bus/usb:/dev/bus/usb
      # Mount host CUPS socket (/etc/cups/client.conf inside devcontainer points here)
      - /run/cups/cups.sock:/run/cups/cups.sock
```

---

## Topic B – Printer on the Same Machine as the Docker Host (Local USB)

Use this setup when the Seiko SLP 650 is plugged directly into a USB port on the same Linux machine that runs Docker.

### Step 1 – Install CUPS and Build Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
  cups \
  cups-client \
  cups-bsd \
  build-essential \
  git \
  libcups2-dev \
  libcupsimage2-dev
```

Ensure the CUPS service is running and enabled on boot:

```bash
sudo systemctl enable --now cups
```

Add your user to the `lpadmin` group so you can manage CUPS queues without `sudo`:

```bash
sudo usermod -aG lpadmin $USER
```

### Step 2 – Build and Install the Seiko SLP 650 Driver

> **CRITICAL – Use the Correct Driver Repository:**
> You **must** use [`fawkesley/smart-label-printer-slp-linux-driver`](https://github.com/fawkesley/smart-label-printer-slp-linux-driver).
> Do **not** use `danieloneill/SeikoSLPLinuxDriver` — see [Important Details & Common Pitfalls](#1-wrong-driver-fork-causes-labels-to-print-sideways-90-rotated) for why.

Clone, compile, and install the driver:

```bash
cd ~
git clone https://github.com/fawkesley/smart-label-printer-slp-linux-driver.git
cd smart-label-printer-slp-linux-driver/src
make build
sudo make install
```

**Fix the CUPS filter ownership and permissions immediately after install:**

```bash
sudo chown root:root /usr/lib/cups/filter/seikoslp.rastertolabel
sudo chmod 755 /usr/lib/cups/filter/seikoslp.rastertolabel
```

*(Why? The driver's `Makefile` uses `mv` instead of `install`, leaving the binary owned by your normal user with `0775` permissions, which CUPS flags as an insecure filter permission error.)*

### Step 3 – Plug In the Printer and Find its USB URI

Connect the SLP 650 via USB, turn it on, and verify Linux detects it:

```bash
lsusb | grep -i -E "0619:0501|seiko"
# Expected: Bus 001 Device 003: ID 0619:0501 Seiko Instruments Inc. SLP650
```

Find the exact CUPS USB device URI:

```bash
sudo lpinfo -v | grep -i usb
# Expected: direct usb://SII/SLP650?serial=32137098B0
```

### Step 4 – Create the Local CUPS Printer Queue

Register the `SLP650` queue using the installed Seiko PPD and configure the default label options:

```bash
sudo lpadmin \
  -p SLP650 \
  -v "usb://SII/SLP650?serial=<YOUR_SERIAL>" \
  -m seiko/siislp650.ppd.gz \
  -o PageSize=MultiPurpose \
  -o Resolution=300dpi \
  -o Density=HighQuality \
  -o FinePrint=True \
  -E

# Set as default printer
sudo lpoptions -d SLP650
```

**What these options do:**
- `-m seiko/siislp650.ppd.gz`: Uses the official SII SLP 650 PPD installed by the driver.
- `-o PageSize=MultiPurpose`: Configures the standard multipurpose label size (`54 × 25 mm` / `51 × 28 mm`).
- `-o Resolution=300dpi`: Matches the SLP 650's native 300 DPI print head and the 602 × 330 px label image.
- `-o Density=HighQuality` & `-o FinePrint=True`: Produces sharp QR codes and text.

### Step 5 – Test Local Printing

```bash
lp -d SLP650 /path/to/repaircafepage/test_label.png
```

---

## Topic C – Printer on a Remote Machine (Raspberry Pi / Linux Print Server)

Use this setup when the Seiko SLP 650 is physically connected via USB to a separate machine on the network (such as a Raspberry Pi Zero W acting as a dedicated print server embedded inside the printer casing) while RepairCafePage runs in Docker on another host.

### Automated Setup Script (Recommended)

A complete, idempotent provisioning script is provided at [`scripts/setup-printserver.sh`](../scripts/setup-printserver.sh). It automates:
- Building and installing the correct driver fork
- Configuring CUPS with ephemeral spools and bounded logging
- Installing **Comitup** for Wi-Fi fallback hotspot and captive portal configuration
- Atomic Wi-Fi profile persistence across power cuts
- Pure ZRAM swap and RAM optimization for 512MB/512MB-constrained Pi Zero boards
- Enabling hardware watchdog (15s) and SSH hardening
- Locking the root and boot filesystems into a read-only overlay (`overlayroot=tmpfs` + read-only `/boot/firmware`) so power can be cut safely at any time.

To provision a fresh or existing Raspberry Pi over SSH:

```bash
# Provision end-to-end and reboot into read-only mode:
ssh printserver "sudo bash -s -- --reboot" < scripts/setup-printserver.sh

# Or provision without activating read-only mode yet (for testing):
ssh printserver "sudo bash -s -- --no-readonly" < scripts/setup-printserver.sh
```

---

### Manual Setup on the Remote Print Server (e.g., Raspberry Pi)

SSH into the print server (e.g., `ssh printserver`) and perform the following steps:

#### 1. Install CUPS and Build the Driver on the Print Server

Follow **Steps 1–3 from [Topic B](#topic-b--printer-on-the-same-machine-as-the-docker-host-local-usb)** on the remote print server:

```bash
sudo apt-get update
sudo apt-get install -y \
  cups cups-client cups-bsd build-essential git libcups2-dev libcupsimage2-dev

cd ~
git clone https://github.com/fawkesley/smart-label-printer-slp-linux-driver.git
cd smart-label-printer-slp-linux-driver/src
make build
sudo make install

# Fix filter ownership and permissions (mandatory!)
sudo chown root:root /usr/lib/cups/filter/seikoslp.rastertolabel
sudo chmod 755 /usr/lib/cups/filter/seikoslp.rastertolabel
```

#### 2. Add and Share the USB Printer Queue on the Print Server

Find the USB URI (`sudo lpinfo -v | grep usb`) and create a shared queue (for example, `SII_SLP650`):

```bash
sudo lpadmin \
  -p SII_SLP650 \
  -v "usb://SII/SLP650?serial=<YOUR_SERIAL>" \
  -m seiko/siislp650.ppd.gz \
  -o printer-is-shared=true \
  -o PageSize=MultiPurpose \
  -o Resolution=300dpi \
  -o Density=HighQuality \
  -o FinePrint=True \
  -E

sudo lpoptions -d SII_SLP650
```

#### 3. Configure CUPS on the Print Server for LAN Sharing

Enable printer sharing and remote access on the print server:

```bash
sudo cupsctl --share-printers --remote-any
```

Next, make sure `ServerAlias *` is present in `/etc/cups/cupsd.conf` so CUPS accepts connections made via IP address or custom SSH hostnames:

```bash
grep -q '^ServerAlias \*' /etc/cups/cupsd.conf || echo 'ServerAlias *' | sudo tee -a /etc/cups/cupsd.conf
sudo systemctl restart cups
```

Confirm your `/etc/cups/cupsd.conf` on the print server includes:

```apache
Port 631
Listen /run/cups/cups.sock
Browsing On
BrowseLocalProtocols dnssd
ServerAlias *

<Location />
  Order allow,deny
  Allow @LOCAL
</Location>
```

Verify the print server listening socket:

```bash
sudo ss -tlnp | grep 631
# Expected: LISTEN 0 ... 0.0.0.0:631 ...
```

---

### Part 2 – Connect the Docker Host to the Remote Print Server

Run these commands on the **Docker host** (the machine where the RepairCafePage containers run):

#### 1. Install CUPS on the Docker Host

The Docker host needs a local `cupsd` instance to provide `/run/cups/cups.sock` for the Docker container and forward jobs over IPP to the print server:

```bash
sudo apt-get update
sudo apt-get install -y cups cups-client cups-bsd
sudo systemctl enable --now cups
sudo usermod -aG lpadmin $USER
```

> **Note:** You do **not** need to compile or install the Seiko driver on the Docker host when using IPP Everywhere (`-m everywhere`). The Docker host sends standard raster data over IPP, and the remote print server runs `seikoslp.rastertolabel`.

#### 2. Verify Connectivity to the Remote Print Server

Replace `192.168.178.223` with your print server's IP address (or `.local` hostname) and `SII_SLP650` with the queue name on the print server:

```bash
curl -I http://192.168.178.223:631/printers/SII_SLP650
# Expected: HTTP/1.1 200 OK
```

#### 3. Create the Local Relay Queue (`SLP650`) on the Docker Host

Add a local queue named `SLP650` that forwards jobs via IPP to the print server:

```bash
lpadmin \
  -p SLP650 \
  -v ipp://192.168.178.223:631/printers/SII_SLP650 \
  -m everywhere \
  -o PageSize=44.45x24.13mm.Borderless \
  -E

lpoptions -d SLP650
```

> **Why `-o PageSize=44.45x24.13mm.Borderless`?**
> When CUPS on the Docker host queries the remote print server's `siislp650.ppd` via IPP Everywhere (`-m everywhere`), the remote `MultiPurpose` page size is translated into the IPP media dimension `44.45x24.13mm.Borderless`. Setting this explicitly prevents the relay queue from defaulting to the narrower `39.88x24.13mm` size.

#### 4. Verify the Relay Queue on the Docker Host

```bash
lpstat -v SLP650
# Expected: device for SLP650: ipp://192.168.178.223:631/printers/SII_SLP650

lpoptions -p SLP650 -l
# Expected: PageSize/Media Size: 39.88x24.13mm.Borderless *44.45x24.13mm.Borderless
```

---

## Important Details & Common Pitfalls (Don't Miss These!)

### 1. Wrong Driver Fork Causes Labels to Print Sideways (90° Rotated)

There are two similarly named Linux driver repositories for Seiko SLP printers on GitHub:
- **CORRECT:** [`fawkesley/smart-label-printer-slp-linux-driver`](https://github.com/fawkesley/smart-label-printer-slp-linux-driver)
- **BROKEN FOR 51×28mm LABELS:** `danieloneill/SeikoSLPLinuxDriver`

In `danieloneill/SeikoSLPLinuxDriver`:
1. `BitMapRotate90(bm, bm)` in `RasterToSIISLP.cxx` is commented out (`//BitMapRotate90(bm, bm);`).
2. `SLP_CMD_FORMFEED` in `SIISLPProcessBitmap.cxx` is removed.

Because RepairCafePage generates a horizontal `602 × 330` px image (`51 mm` wide × `28 mm` high) and the physical label roll feeds vertically (`28 mm` wide across the thermal head × `51 mm` feed length), the driver **must** rotate the bitmap 90° before sending scanlines to the print head and issue a form-feed command at the end of the label. If your label prints sideways across the narrow width of the label, you have the wrong driver fork installed on the machine with the USB printer.

### 2. CUPS Filter Permissions (`seikoslp.rastertolabel`)

In `fawkesley/smart-label-printer-slp-linux-driver/src/Makefile`, the `install` target runs:
```makefile
mv seikoslp.rastertolabel /usr/lib/cups/filter/
```
Because `make build` is executed as a normal user, `mv` preserves your user's UID/GID and `0775` permissions. CUPS enforces strict security checks on `/usr/lib/cups/filter/*` and will fail with `File "/usr/lib/cups/filter/seikoslp.rastertolabel" has insecure permissions` if it is group-writable or not owned by `root:root`.

Always run after `sudo make install`:
```bash
sudo chown root:root /usr/lib/cups/filter/seikoslp.rastertolabel
sudo chmod 755 /usr/lib/cups/filter/seikoslp.rastertolabel
```

### 3. Missing `ServerAlias *` on Remote Print Server (`HTTP 400 Bad Request`)

By default, CUPS validates the HTTP `Host:` header against the machine's local hostname (`<hostname>.local` or `localhost`). When the Docker host connects to a remote print server using an IP address (`ipp://192.168.178.223:631/...`), the remote CUPS daemon rejects the request with `400 Bad Request`, causing `lpadmin -m everywhere` to fail with:
```text
lpadmin: Unable to connect to "192.168.178.223:631": Operation now in progress
```
Adding `ServerAlias *` to `/etc/cups/cupsd.conf` on the remote print server resolves this.

### 4. Static IP or DHCP Reservation for the Remote Print Server

If you use an IP address in `ipp://<IP>:631/printers/SII_SLP650`, assign a **static IP / DHCP reservation** to the Raspberry Pi print server in your router (e.g., Fritz!Box -> Home Network -> Network -> Edit device -> "Always assign this network device the same IPv4 address"). Otherwise, if the print server's IP changes, print jobs on the Docker host will hang waiting for the old IP.

### 5. QR Code Target URL (`app_url` / `PUBLIC_URL`) and Custom Label Logo

Each printed label includes a QR code pointing to `<app_url>/edit/<qr_token>` so repairers can scan the label with a smartphone or tablet to open the repair record directly.
- Look at [`app/api/repairs.py`](../app/api/repairs.py): it uses `app_url` from the application settings (`config.json` / Admin UI), falling back to the incoming HTTP `Host` header.
- **Make sure `app_url` in Admin Settings** is set to the actual LAN IP/hostname or domain of your RepairCafePage instance (e.g., `http://192.168.178.50` or `https://repaircafe.example.org`), **not** `http://localhost`, otherwise phones scanning the printed QR code will try to open `localhost` on the phone itself.
- **Custom Logo:** To print your own Repair Café logo on the bottom-left of the label instead of the default logo, place a square PNG file at `/data/logo.png` inside the `app_data` volume (or configure `org_name` and `org_website` in Admin Settings).

### 6. Re-enabling a Paused Queue After Printer Power-Off

If a print job is sent while the SLP 650 is switched off, out of labels, or unplugged from USB, CUPS may pause the printer queue (`Printer SLP650 disabled since ...`). Once the printer is turned back on, clear stuck jobs and re-enable the queue:

```bash
# Clear any stuck jobs and re-enable the queue
cancel -a SLP650
cupsenable SLP650
cupsaccept SLP650
```

*(If using a remote print server, run the same commands for `SII_SLP650` on the print server if its queue was paused).*

---

## Verification & Troubleshooting

When diagnosing printing issues, test from the bottom layer (closest to the hardware) up to the Docker container:

### Layer 1 – Test Directly on the Print Server (USB Host)

```bash
# 1. Check USB connection
lsusb | grep -i 0619:0501

# 2. Check queue status
lpstat -p -d

# 3. Print a test label PNG directly
lp -d SII_SLP650 test_label.png
```

### Layer 2 – Test from the Docker Host

```bash
# 1. Check CUPS scheduler and queue status
lpstat -r
lpstat -p -d
lpstat -v SLP650

# 2. Print the repository's test label from the Docker host
lp -d SLP650 /path/to/repaircafepage/test_label.png
```

### Layer 3 – Test from Inside the Docker Backend Container

```bash
# 1. Verify the container can reach the host CUPS socket
docker compose exec backend lpstat -r
# Expected: scheduler is running

# 2. Verify the SLP650 queue is visible inside the container
docker compose exec backend lpstat -p -d
# Expected: printer SLP650 is idle. enabled since ...

# 3. Trigger a test print using Python inside the container
docker compose exec backend python -c "
from app.services.label_service import LabelService
svc = LabelService('SLP650')
res = svc.print_label(
    {'id': 42, 'qr_token': 'test-token', 'datum': '2026-10-30', 'vorname': 'Max', 'nachname': 'Mustermann', 'geraet_art': 'Toaster'},
    app_url='https://repaircafe.example.org',
    org_name='Repair Café',
    org_website='repaircafe.example.org'
)
print(res)
"
```

### Inspecting CUPS Logs

If jobs fail with `Filter failed` or disappear without printing, enable CUPS debug logging on the machine where the job failed (Docker host or remote print server) and inspect `/var/log/cups/error_log`:

```bash
sudo cupsctl --debug-logging
sudo tail -f /var/log/cups/error_log
```

Once troubleshooting is complete, disable verbose debug logging:

```bash
sudo cupsctl --no-debug-logging
```

---

## Remote Print Server Maintenance & Wi-Fi Configuration

When using the hardened, read-only setup on a remote Raspberry Pi (e.g. Raspberry Pi Zero W enclosed inside the printer):

### 1. Wi-Fi Configuration via Captive Portal (Comitup)

If you transport the printer to a new location or event where the previous Wi-Fi is out of range:
1. Power on the printer (and the Pi Zero W inside).
2. The Pi will attempt to connect to known Wi-Fi networks for ~30 seconds.
3. If no known network is found, it automatically starts a Wi-Fi Access Point named `labelprinter-<nnn>`.
4. Connect to the `labelprinter-<nnn>` network using your phone or laptop.
5. A captive portal popup will appear automatically (or navigate to `http://10.41.0.1` in your browser).
6. Select the local Wi-Fi network, enter the Wi-Fi password, and submit.
7. The Pi immediately connects to the new network and shuts down the hotspot.
8. The `persist-nmconnections` path watcher automatically syncs the new connection profile to the underlying SD card so it persists across future power cuts.

> [!TIP]
> **Use mDNS (`labelprinter.local`) on the Docker Host:**
> Because the printer will receive a different IP address from DHCP on a new Wi-Fi network, configure the local queue on your Docker host using mDNS:
> ```bash
> lpadmin -p SLP650 -v ipp://labelprinter.local:631/printers/SII_SLP650 -m everywhere -o PageSize=44.45x24.13mm.Borderless -E
> ```
> This way, the Docker host can always communicate with the print server without manually editing IP addresses.

### 2. Checking System Status on the Print Server

SSH into the print server and run the included status tool:

```bash
ssh printserver "sudo ro-status"
```

This displays:
- Mount options for `/`, `/media/root-ro`, and `/boot/firmware`
- Memory and ZRAM swap status
- Active Wi-Fi SSID and `comitup` service state
- CUPS printer queue readiness

### 3. Making Persistent Changes / System Updates

Because `overlayroot=tmpfs` discards any changes written to `/` upon power-down:

#### Option A: One-off edits via `overlayroot-chroot`
To make quick persistent configuration changes to the underlying SD card without rebooting:
```bash
sudo overlayroot-chroot
# You are now in a chroot directly on the read-write underlying partition
nano /etc/...
exit
```

#### Option B: Disabling overlay mode for full system updates
To run system upgrades (`apt update && apt upgrade`) or run the setup script again:
```bash
# 1. Disable read-only overlay and boot partition:
sudo raspi-config nonint disable_overlayfs
sudo raspi-config nonint disable_bootro
sudo reboot

# 2. Perform your updates:
sudo apt update && sudo apt upgrade -y

# 3. Re-enable read-only mode and reboot:
sudo raspi-config nonint enable_bootro
sudo raspi-config nonint enable_overlayfs
sudo reboot
```
