#!/usr/bin/env bash
# ==============================================================================
# RepairCafePage — Raspberry Pi Print Server Setup & Hardening Script
# ==============================================================================
# Configures a fresh or existing Raspberry Pi OS (Bookworm / Trixie, including
# Raspberry Pi Zero W armv6l) as a dedicated, hardened, read-only CUPS print
# server for the Seiko Instruments Smart Label Printer 650 (SII SLP 650) with
# a Comitup Wi-Fi fallback hotspot & captive portal.
#
# Usage:
#   Remotely over SSH:
#     ssh printserver "sudo bash -s -- --reboot" < scripts/setup-printserver.sh
#
#   Locally on the Raspberry Pi:
#     sudo bash scripts/setup-printserver.sh [--no-readonly] [--reboot] [--ap-password <pw>]
# ==============================================================================

set -euo pipefail

ENABLE_READONLY=true
AUTO_REBOOT=false
AP_PASSWORD=""
PRINTER_QUEUE="SII_SLP650"
DRIVER_REPO="https://github.com/fawkesley/smart-label-printer-slp-linux-driver.git"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-readonly)
      ENABLE_READONLY=false
      shift
      ;;
    --reboot)
      AUTO_REBOOT=true
      shift
      ;;
    --ap-password)
      AP_PASSWORD="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--no-readonly] [--reboot] [--ap-password <password>]" >&2
      exit 1
      ;;
  esac
done

log() {
  echo -e "\n[setup-printserver] === $* ==="
}

if [[ "${EUID}" -ne 0 ]]; then
  echo "Error: Please run this script as root (e.g. via sudo)." >&2
  exit 1
fi

# ------------------------------------------------------------------------------
# 1. Pre-flight Check: Ensure OverlayFS is not currently active
# ------------------------------------------------------------------------------
log "1/9 Pre-flight checks"
if grep -qw "overlayroot=tmpfs" /proc/cmdline || findmnt -n -o FSTYPE / 2>/dev/null | grep -qw "overlay"; then
  echo "ERROR: Root filesystem is currently mounted as a read-only overlay (overlayroot)." >&2
  echo "To run setup or apply persistent updates, first disable overlayfs and reboot:" >&2
  echo "  sudo raspi-config nonint disable_overlayfs" >&2
  echo "  sudo raspi-config nonint disable_bootro" >&2
  echo "  sudo reboot" >&2
  exit 1
fi

# Remount /boot/firmware rw if it was mounted ro
if findmnt -n -o OPTIONS /boot/firmware 2>/dev/null | grep -qw ro; then
  mount -o remount,rw /boot/firmware
fi

# ------------------------------------------------------------------------------
# 2. Disable Wi-Fi Power Saving Immediately (Fixes Pi Zero W brcmfmac lag/drops)
# ------------------------------------------------------------------------------
log "2/9 Disabling Wi-Fi power management for reliable LAN connectivity"
mkdir -p /etc/NetworkManager/conf.d
cat <<'EOF' > /etc/NetworkManager/conf.d/10-wifi-powersave-off.conf
[connection]
# 2 = disable Wi-Fi power saving (prevents brcmfmac sleep/packet loss on Pi Zero W)
wifi.powersave = 2
EOF

if command -v iw >/dev/null 2>&1 && ip link show wlan0 >/dev/null 2>&1; then
  iw dev wlan0 set power_save off || true
fi

# ------------------------------------------------------------------------------
# 3. Pre-configure Comitup & Install Required System Packages
# ------------------------------------------------------------------------------
log "3/9 Installing CUPS, build tools, Comitup captive portal, and overlayroot"

# Pre-seed /etc/comitup.conf before apt installs comitup so its first start uses our settings
cat <<EOF > /etc/comitup.conf
# Comitup Wi-Fi fallback hotspot & captive portal configuration
ap_name: <hostname>
ap_password: ${AP_PASSWORD}
enable_appliance_mode: true
external_callback: /usr/local/sbin/persist-wifi-to-ro
verbose: 0
enable_nuke: 0
EOF

# Install persist-wifi-to-ro before comitup starts so external_callback exists
cat <<'EOF' > /usr/local/sbin/persist-wifi-to-ro
#!/usr/bin/env bash
# Atomically persists NetworkManager Wi-Fi connection profiles & Comitup state
# to the underlying SD card partition (/media/root-ro) when overlayroot is active.
set -euo pipefail

if ! mountpoint -q /media/root-ro; then
  # Not running in overlayroot mode; files are already written directly to disk.
  exit 0
fi

# Prevent concurrent executions
exec 9>/run/persist-wifi-to-ro.lock
flock -w 10 9 || exit 0

mount -o remount,rw /media/root-ro 2>/dev/null || true
cleanup() {
  sync
  mount -o remount,ro /media/root-ro 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p /media/root-ro/etc/NetworkManager/system-connections
rsync -a --delete \
  /etc/NetworkManager/system-connections/ \
  /media/root-ro/etc/NetworkManager/system-connections/
chmod 700 /media/root-ro/etc/NetworkManager/system-connections
chmod 600 /media/root-ro/etc/NetworkManager/system-connections/* 2>/dev/null || true

if [[ -d /var/lib/comitup ]]; then
  mkdir -p /media/root-ro/var/lib/comitup
  rsync -a /var/lib/comitup/ /media/root-ro/var/lib/comitup/
fi

logger -t persist-wifi-to-ro "Synced Wi-Fi profiles to /media/root-ro"
EOF
chmod 755 /usr/local/sbin/persist-wifi-to-ro

export DEBIAN_FRONTEND=noninteractive
export APT_LISTCHANGES_FRONTEND=none
apt-get update
apt-get install -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" --no-install-recommends \
  cups \
  cups-client \
  cups-bsd \
  build-essential \
  git \
  ca-certificates \
  libcups2-dev \
  libcupsimage2-dev \
  comitup \
  overlayroot \
  rsync \
  avahi-daemon \
  iw

# ------------------------------------------------------------------------------
# 4. Build & Install Seiko SLP 650 Driver (fawkesley fork with 90-deg rotation)
# ------------------------------------------------------------------------------
log "4/9 Building & installing Seiko SLP 650 CUPS driver (fawkesley fork)"
BUILD_DIR="$(mktemp -d /tmp/slp-driver.XXXXXX)"
git clone --depth 1 "${DRIVER_REPO}" "${BUILD_DIR}"
pushd "${BUILD_DIR}/src" >/dev/null
make build
make install
popd >/dev/null
rm -rf "${BUILD_DIR}"

# Critical fix: Makefile uses `mv`, which preserves build ownership/permissions.
# CUPS requires filters to be owned by root:root with 0755 permissions.
chown root:root /usr/lib/cups/filter/seikoslp.rastertolabel
chmod 755 /usr/lib/cups/filter/seikoslp.rastertolabel

# ------------------------------------------------------------------------------
# 5. Configure CUPS Daemon & SII_SLP650 Shared Queue
# ------------------------------------------------------------------------------
log "5/9 Configuring CUPS daemon (ephemeral spool, bounded logs, LAN sharing)"
systemctl enable --now cups

cat <<'EOF' > /etc/cups/cupsd.conf
# Hardened & RAM-friendly CUPS configuration for embedded Raspberry Pi print server
LogLevel warn
PageLogFormat
# Cap log files at 1 MiB so /var/log/cups never fills tmpfs RAM
MaxLogSize 1m
# Immediately purge job history and spool files after printing to save RAM
PreserveJobHistory No
PreserveJobFiles No
MaxJobs 25
# Automatically retry transient USB errors instead of disabling the queue
ErrorPolicy retry-current-job
JobRetryInterval 5
JobRetryLimit 5

Port 631
Listen /run/cups/cups.sock
Browsing On
BrowseLocalProtocols dnssd
DefaultAuthType Basic
WebInterface Yes
# Allow connections by IP address, custom SSH host Alias, or .local mDNS name
ServerAlias *

<Location />
  Order allow,deny
  Allow localhost
  Allow @LOCAL
</Location>

<Location /printers>
  Order allow,deny
  Allow localhost
  Allow @LOCAL
</Location>

<Location /admin>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow localhost
  Allow @LOCAL
</Location>

<Location /admin/conf>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow localhost
  Allow @LOCAL
</Location>

<Location /admin/log>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow localhost
  Allow @LOCAL
</Location>

<Policy default>
  JobPrivateAccess default
  JobPrivateValues default
  SubscriptionPrivateAccess default
  SubscriptionPrivateValues default
  <Limit Create-Job Print-Job Print-URI Validate-Job>
    Order deny,allow
  </Limit>
  <Limit Send-Document Send-URI Hold-Job Release-Job Restart-Job Purge-Jobs Set-Job-Attributes Create-Job-Subscription Renew-Subscription Cancel-Subscription Get-Notifications Reprocess-Job Cancel-Current-Job Suspend-Current-Job Resume-Job Cancel-My-Jobs Close-Job CUPS-Move-Job>
    Require user @OWNER @SYSTEM
    Order deny,allow
  </Limit>
  <Limit CUPS-Get-Document>
    AuthType Default
    Require user @OWNER @SYSTEM
    Order deny,allow
  </Limit>
  <Limit CUPS-Add-Modify-Printer CUPS-Delete-Printer CUPS-Add-Modify-Class CUPS-Delete-Class CUPS-Set-Default CUPS-Get-Devices>
    AuthType Default
    Require user @SYSTEM
    Order deny,allow
  </Limit>
  <Limit Pause-Printer Resume-Printer Enable-Printer Disable-Printer Pause-Printer-After-Current-Job Hold-New-Jobs Release-Held-New-Jobs Deactivate-Printer Activate-Printer Restart-Printer Shutdown-Printer Startup-Printer Promote-Job Schedule-Job-After Cancel-Jobs CUPS-Accept-Jobs CUPS-Reject-Jobs>
    AuthType Default
    Require user @SYSTEM
    Order deny,allow
  </Limit>
  <Limit Cancel-Job CUPS-Authenticate-Job>
    Require user @OWNER @SYSTEM
    Order deny,allow
  </Limit>
  <Limit All>
    Order deny,allow
  </Limit>
</Policy>
EOF

systemctl restart cups

# Discover USB URI of connected SII SLP650 (or keep existing URI if unplugged)
USB_URI="$(lpinfo -v 2>/dev/null | grep -o 'usb://SII/SLP650[^[:space:]]*' | head -n1 || true)"
if [[ -z "${USB_URI}" ]]; then
  EXISTING_URI="$(lpstat -v "${PRINTER_QUEUE}" 2>/dev/null | awk '{print $NF}' || true)"
  if [[ "${EXISTING_URI}" == usb://* ]]; then
    USB_URI="${EXISTING_URI}"
  else
    USB_URI="usb://SII/SLP650"
  fi
fi

log "Configuring CUPS queue ${PRINTER_QUEUE} (${USB_URI})"
lpadmin \
  -p "${PRINTER_QUEUE}" \
  -v "${USB_URI}" \
  -m seiko/siislp650.ppd.gz \
  -o printer-is-shared=true \
  -o PageSize=MultiPurpose \
  -o Resolution=300dpi \
  -o Density=HighQuality \
  -o FinePrint=True \
  -E

lpoptions -d "${PRINTER_QUEUE}"
cupsenable "${PRINTER_QUEUE}" || true
cupsaccept "${PRINTER_QUEUE}" || true

# Add primary non-root user (if any) to lpadmin
if id -u mojo >/dev/null 2>&1; then
  usermod -aG lpadmin mojo
fi

# Systemd oneshot service to guarantee queue is enabled on every boot
cat <<EOF > /etc/systemd/system/cups-ensure-enabled.service
[Unit]
Description=Ensure CUPS printer queue ${PRINTER_QUEUE} is enabled and accepting jobs
After=cups.service
Requires=cups.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c '/usr/sbin/cupsenable ${PRINTER_QUEUE} || true; /usr/sbin/cupsaccept ${PRINTER_QUEUE} || true'

[Install]
WantedBy=multi-user.target
EOF

# ------------------------------------------------------------------------------
# 6. Configure Atomic Read-Only Persistence for New Wi-Fi Networks
# ------------------------------------------------------------------------------
log "6/9 Installing systemd path watcher to persist new Wi-Fi networks to SD card"

# Remove hardcoded `interface-name=wlan0` from existing Wi-Fi profiles if needed by Comitup,
# or keep standard NM permissions so Comitup can manage wlan0 seamlessly.
cat <<'EOF' > /etc/systemd/system/persist-nmconnections.path
[Unit]
Description=Watch /etc/NetworkManager/system-connections for new/updated Wi-Fi profiles

[Path]
PathChanged=/etc/NetworkManager/system-connections
PathModified=/etc/NetworkManager/system-connections

[Install]
WantedBy=multi-user.target
EOF

cat <<'EOF' > /etc/systemd/system/persist-nmconnections.service
[Unit]
Description=Persist NetworkManager Wi-Fi profiles to read-only root partition
After=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/persist-wifi-to-ro
EOF

systemctl daemon-reload
systemctl enable --now cups-ensure-enabled.service
systemctl enable --now persist-nmconnections.path
systemctl enable comitup.service

# ------------------------------------------------------------------------------
# 7. Memory, ZRAM Swap & Background Timer Optimization (Pi Zero W 426 MiB RAM)
# ------------------------------------------------------------------------------
log "7/9 Optimizing swap (pure zram), journald (16M volatile), and disabling disk-write timers"

mkdir -p /etc/rpi/swap.conf.d
cat <<'EOF' > /etc/rpi/swap.conf.d/readonly.conf
# Use pure in-RAM compressed swap (no /var/swap backing file on tmpfs)
[Main]
Mechanism=zram
EOF

# Remove /var/swap file so it does not consume space or get copied into tmpfs
rm -f /var/swap

# Cap systemd-journald in volatile RAM (/run/log/journal) at 16 MiB
mkdir -p /etc/systemd/journald.conf.d
cat <<'EOF' > /etc/systemd/journald.conf.d/volatile.conf
[Journal]
Storage=volatile
RuntimeMaxUse=16M
RuntimeMaxFileSize=4M
EOF
systemctl restart systemd-journald
rm -rf /var/log/journal

# Disable background timers & services that consume RAM or attempt disk maintenance
for unit in \
  apt-daily.timer \
  apt-daily-upgrade.timer \
  man-db.timer \
  dpkg-db-backup.timer \
  logrotate.timer \
  fstrim.timer \
  e2scrub_all.timer \
  rpi-zram-writeback.timer \
  bluetooth.service \
  colord.service; do
  if systemctl list-unit-files "${unit}" >/dev/null 2>&1; then
    systemctl disable --now "${unit}" 2>/dev/null || true
  fi
done

# Clean up old temporary build directories and APT caches
rm -rf /home/mojo/smart-label-printer-slp-linux-driver /root/smart-label-printer-slp-linux-driver
apt-get autoremove -y --purge
apt-get clean
rm -rf /var/lib/apt/lists/* /var/log/cups/* /var/spool/cups/c* /var/spool/cups/d* 2>/dev/null || true

# ------------------------------------------------------------------------------
# 8. Hardware Watchdog, SSH Hardening & Status Helper Script
# ------------------------------------------------------------------------------
log "8/9 Enabling BCM2835 hardware watchdog, SSH hardening, and ro-status tool"

mkdir -p /etc/systemd/system.conf.d
cat <<'EOF' > /etc/systemd/system.conf.d/watchdog.conf
[Manager]
RuntimeWatchdogSec=15s
RebootWatchdogSec=2min
EOF

# Only disable SSH password login if at least one non-empty authorized_keys file exists
if find /home /root -maxdepth 3 -path "*/.ssh/authorized_keys" -size +0c 2>/dev/null | grep -q .; then
  mkdir -p /etc/ssh/sshd_config.d
  cat <<'EOF' > /etc/ssh/sshd_config.d/hardening.conf
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
UseDNS no
EOF
  systemctl reload ssh || systemctl restart ssh
else
  echo "Notice: No non-empty authorized_keys found; keeping SSH password auth enabled to prevent lockout."
fi

cat <<'EOF' > /usr/local/sbin/ro-status
#!/usr/bin/env bash
echo "=== Print Server Read-Only & System Status ==="
echo -n "Root FS (/):          "
findmnt -n -o SOURCE,FSTYPE,OPTIONS /
if mountpoint -q /media/root-ro; then
  echo -n "Lower SD (/media/root-ro): "
  findmnt -n -o SOURCE,FSTYPE,OPTIONS /media/root-ro
fi
echo -n "Boot FS (/boot/firmware):  "
findmnt -n -o SOURCE,FSTYPE,OPTIONS /boot/firmware 2>/dev/null || echo "not mounted"
echo ""
echo "=== Memory & ZRAM Swap ==="
free -h
echo -n "zram0 backing_dev:    "
cat /sys/block/zram0/backing_dev 2>/dev/null || echo "n/a"
echo ""
echo "=== Network & Comitup ==="
nmcli -t -f NAME,TYPE,DEVICE,STATE connection show --active 2>/dev/null || true
echo -n "comitup.service:      "
systemctl is-active comitup.service 2>/dev/null || true
echo -n "wifi-persist watcher: "
systemctl is-active persist-nmconnections.path 2>/dev/null || true
echo ""
echo "=== CUPS Printer Queue ==="
lpstat -p -d 2>/dev/null || true
EOF
chmod 755 /usr/local/sbin/ro-status

# ------------------------------------------------------------------------------
# 9. Enable Read-Only Root (overlayroot) & Read-Only Boot Partition
# ------------------------------------------------------------------------------
if [[ "${ENABLE_READONLY}" == "true" ]]; then
  log "9/9 Enabling read-only /boot/firmware and overlayroot=tmpfs"
  cat <<'EOF' > /etc/overlayroot.conf
overlayroot_cfgdisk="disabled"
overlayroot=""
EOF
  cat <<'EOF' > /etc/overlayroot.local.conf
overlayroot="tmpfs:swap=1,recurse=0"
EOF
  sed -i 's/defaults,noatime/defaults,ro,noatime/' /etc/fstab || true
  raspi-config nonint enable_bootro
  raspi-config nonint enable_overlayfs
  sync
  log "Setup complete! Read-only overlayroot and bootro are configured for next boot."
else
  log "9/9 Skipping read-only activation (--no-readonly specified)."
fi

if [[ "${AUTO_REBOOT}" == "true" ]]; then
  log "Rebooting now to activate read-only overlay filesystem..."
  nohup bash -c "sleep 2 && reboot" >/dev/null 2>&1 &
  exit 0
else
  echo "Run 'sudo reboot' to activate the read-only filesystem."
fi
