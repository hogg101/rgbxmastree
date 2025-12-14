#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--update" ]]; then
  # Fast path: skip OS deps + venv recreation; just sync code, pip install, restart.
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  exec "${SCRIPT_DIR}/update_pi.sh"
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run with sudo: sudo $0"
  exit 1
fi

INSTALL_DIR="/opt/rgbxmastree"
CONFIG_DIR="/var/lib/rgbxmastree"
CONFIG_PATH="${CONFIG_DIR}/config.json"
SERVICE_NAME="rgbxmastree.service"

INSTALL_USER="${SUDO_USER:-}"
if [[ -z "${INSTALL_USER}" || "${INSTALL_USER}" == "root" ]]; then
  # Best-effort fallback
  INSTALL_USER="$(logname 2>/dev/null || true)"
fi
if [[ -z "${INSTALL_USER}" || "${INSTALL_USER}" == "root" ]]; then
  echo "Could not determine non-root install user. Run with sudo from your normal user session."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Installing OS dependencies"
apt-get update -y
apt-get install -y --no-install-recommends \
  python3 \
  python3-venv \
  python3-pip \
  python3-gpiozero \
  python3-colorzero

echo "==> Enabling SPI (required for the tree)"
if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_spi 0 || true
else
  echo "raspi-config not found; ensure SPI is enabled manually."
fi

echo "==> Installing app to ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
rsync -a --delete \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".git" \
  "${REPO_DIR}/" "${INSTALL_DIR}/"
chown -R "${INSTALL_USER}:${INSTALL_USER}" "${INSTALL_DIR}"

echo "==> Creating venv and installing Python deps"
sudo -u "${INSTALL_USER}" bash -lc "
  cd '${INSTALL_DIR}'
  python3 -m venv .venv
  . .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
"

echo "==> Creating config dir at ${CONFIG_DIR}"
mkdir -p "${CONFIG_DIR}"
chown -R "${INSTALL_USER}:${INSTALL_USER}" "${CONFIG_DIR}"
if [[ ! -f "${CONFIG_PATH}" ]]; then
  cat > "${CONFIG_PATH}" <<'JSON'
{
  "countdown_until": null,
  "mode": "auto",
  "program_id": "rgb_cycle",
  "program_speed": 1.0,
  "schedule": {
    "days": null,
    "end_hhmm": "23:00",
    "start_hhmm": "07:30"
  }
}
JSON
  chown "${INSTALL_USER}:${INSTALL_USER}" "${CONFIG_PATH}"
fi

echo "==> Installing systemd service"
SERVICE_TEMPLATE="${INSTALL_DIR}/scripts/rgbxmastree.service"
SERVICE_OUT="/etc/systemd/system/${SERVICE_NAME}"

sed \
  -e "s|{{USER}}|${INSTALL_USER}|g" \
  -e "s|{{INSTALL_DIR}}|${INSTALL_DIR}|g" \
  "${SERVICE_TEMPLATE}" > "${SERVICE_OUT}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo
echo "==> Done"
echo "Open: http://xmaspi.local:8080"
echo "Service status: sudo systemctl status ${SERVICE_NAME} --no-pager"
echo "Logs: sudo journalctl -u ${SERVICE_NAME} -f"

if [[ -f /proc/device-tree/model ]] && grep -qi raspberry /proc/device-tree/model; then
  echo
  echo "Note: If this was the first time enabling SPI, a reboot may be required."
fi


