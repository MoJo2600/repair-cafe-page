# CUPS Network Printing Setup

This guide explains how to configure the Docker host machine so that the
application container can print labels to a USB printer (SLP 650) that is
physically connected to **another machine** on the local network — either a
Linux machine sharing it via CUPS/IPP, or a Windows machine sharing it via
the Windows print spooler (SMB).

## Overview

```
                                                    ┌──────────────────────────┐
                                                    │  Printer host machine    │
                                                    │                          │
                                                    │  Option A (Linux/CUPS):  │
┌──────────────────────┐   ┌──────────────────────┐ │  cupsd  ◄── USB  SLP650  │
│  Docker Container    │   │  Docker Host (CUPS)  │ │                          │
│                      │   │                      │ │  Option B (Windows):     │
│  lp -d SLP650  ──────►631│──► ipp://host/SLP650 ─►│  Print Spooler ◄─ USB    │
│  (cups-client)       │IPP│  or smb://host/SLP650│ │  SLP650                  │
└──────────────────────┘   └──────────────────────┘ └──────────────────────────┘
```

The container only ever talks to the **host CUPS server** via IPP on port 631.
CUPS on the host forwards the job to the remote printer using either IPP
(Linux/CUPS sharing) or SMB (Windows sharing).

---

## Prerequisites

- The Docker host machine runs a Linux distribution with CUPS installed.
- The SLP 650 is connected via USB to another machine on the LAN that shares it
  (Linux with CUPS, or Windows with printer sharing enabled).
- The sharing machine is reachable from the Docker host (verify with `ping`).

---

## Step 1 – Install CUPS on the Host (if not present)

```bash
# Debian / Ubuntu
sudo apt-get update && sudo apt-get install -y cups

# Fedora / RHEL
sudo dnf install cups
```

---

## Step 2 – Configure CUPS to Accept Connections from Docker

Edit `/etc/cups/cupsd.conf`:

```bash
sudo nano /etc/cups/cupsd.conf
```

Find or add the following directives:

```apache
# Listen on all interfaces so the Docker container can reach CUPS
Listen *:631

# Allow Docker containers (172.16.0.0/12 covers the default Docker bridge range)
<Location />
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 172.16.0.0/12
</Location>

<Location /admin>
  Order allow,deny
  Allow from 127.0.0.1
  Allow from 172.16.0.0/12
</Location>
```

Restart CUPS:

```bash
sudo systemctl restart cups
```

Verify that CUPS is listening on all interfaces:

```bash
sudo ss -tlnp | grep 631
# Expected: tcp   LISTEN   0   ...   0.0.0.0:631   ...
```

---

## Step 3 – Add the Shared Printer to Host CUPS

CUPS needs a printer queue that points to the remote machine sharing the SLP 650.
Choose the option that matches how the printer is shared.

---

### Option A – Printer shared via CUPS on another Linux machine

The other Linux machine must have the SLP 650 configured in its own CUPS and
have printer sharing enabled (default in most distros). CUPS shares printers
over IPP on port 631.

**On the sharing machine** – verify sharing is on:

```bash
# The printer should be browseable/shared
lpstat -p -d
# Optionally confirm IPP is accessible:
curl http://localhost:631/printers/
```

If sharing is off, enable it in `/etc/cups/cupsd.conf` on the sharing machine:

```apache
# Allow remote access to the printer
<Location /printers>
  Order allow,deny
  Allow from 127.0.0.1
  Allow from @LOCAL         # all machines on the local LAN
</Location>
```

Then restart CUPS on the sharing machine: `sudo systemctl restart cups`

**On the Docker host** – add the remote printer queue:

```bash
sudo lpadmin \
  -p SLP650 \
  -v ipp://192.168.1.50:631/printers/SLP650 \
  -E \
  -m everywhere

# Set as default (optional)
sudo lpoptions -d SLP650
```

Replace `192.168.1.50` with the IP of the machine that has the printer, and
`SLP650` in the URI with whatever the queue is named on that machine
(`lpstat -p` on the sharing machine shows the queue name).

---

### Option B – Printer shared via Windows

Windows must have the SLP 650 installed and **printer sharing enabled** in the
printer properties.

**On the Docker host** – install the Samba CUPS backend if not present:

```bash
# Debian / Ubuntu
sudo apt-get install -y cups-smb smbclient

# Fedora / RHEL
sudo dnf install cups samba-client
```

**Add the Windows shared printer queue:**

```bash
sudo lpadmin \
  -p SLP650 \
  -v smb://WINDOWS-PC/SLP650 \
  -E \
  -m everywhere

# Set as default (optional)
sudo lpoptions -d SLP650
```

Replace `WINDOWS-PC` with the Windows hostname or IP address, and `SLP650`
with the exact share name configured in Windows printer properties.

If the Windows share requires credentials:

```bash
sudo lpadmin \
  -p SLP650 \
  -v smb://username:password@WINDOWS-PC/SLP650 \
  -E \
  -m everywhere
```

> **Note:** Use the Windows local username/password, not a domain account,
> unless Kerberos/domain auth is configured on the host.

---

### Verifying the queue URI after adding

```bash
# Confirm the queue was created with the correct URI
lpstat -v SLP650
# Expected: device for SLP650: ipp://... or smb://...
```

---

## Step 4 – Verify the Printer Queue

```bash
# List all queues
lpstat -p -d

# Send a test page
echo "test" | lp -d SLP650

# Check the queue for errors
lpq -P SLP650
```

---

## Step 5 – Application Configuration

In your `.env` file (or `docker-compose.yml` environment section):

```bash
LABEL_PRINTER_ENABLED=true
LABEL_PRINTER_NAME=SLP650   # must match the CUPS queue name from Step 3
```

The container's `CUPS_SERVER` is already set to `host.docker.internal:631`
in `docker-compose.yml`, so no further container configuration is needed.

---

## Troubleshooting

### Container cannot reach host CUPS

```bash
# Inside the container
lpstat -r
# Expected: scheduler is running

lpstat -p -d
# Should list SLP650
```

If `lpstat -r` returns an error, check that:
- CUPS on the host is running: `sudo systemctl status cups`
- Port 631 is reachable: `telnet <host-ip> 631` from inside the container
- The `<Location />` block in `cupsd.conf` allows the container's IP range

### Jobs are queued but not printed

```bash
# On the host
sudo tail -f /var/log/cups/error_log

# Option A – test IPP connectivity to the sharing machine
curl -v http://192.168.1.50:631/printers/SLP650

# Option B – test SMB connectivity to Windows
smbclient -L //WINDOWS-PC -U username
```

Common causes:
- Wrong URI in the CUPS queue — remove and re-add with `sudo lpadmin -x SLP650`
  then repeat Step 3
- Firewall on the sharing machine blocking port 631 (IPP) or 445 (SMB)
- Windows printer sharing not enabled, or the share name contains spaces
  (use quotes: `smb://PC/"My Printer"`)
- Printer is in power-save / sleep mode

### Permission denied when adding a printer

```bash
# Add your user to the lpadmin group, then log out and back in
sudo usermod -a -G lpadmin $USER
sudo systemctl restart cups
```
