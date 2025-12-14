#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run with sudo: sudo $0"
  exit 1
fi

INSTALL_DIR="/opt/rgbxmastree"
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

echo "==> Updating app in ${INSTALL_DIR}"
if [[ ! -d "${INSTALL_DIR}" ]]; then
  echo "Install dir ${INSTALL_DIR} not found. Run scripts/setup_pi.sh first."
  exit 1
fi

rsync -a --delete \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".git" \
  "${REPO_DIR}/" "${INSTALL_DIR}/"
chown -R "${INSTALL_USER}:${INSTALL_USER}" "${INSTALL_DIR}"

echo "==> Ensuring systemd service matches template (if changed)"
SERVICE_TEMPLATE="${INSTALL_DIR}/scripts/rgbxmastree.service"
SERVICE_OUT="/etc/systemd/system/${SERVICE_NAME}"
if [[ ! -f "${SERVICE_TEMPLATE}" ]]; then
  echo "Missing service template at ${SERVICE_TEMPLATE}. Is ${INSTALL_DIR} a valid install?"
  exit 1
fi

tmp_unit="$(mktemp)"
cleanup() {
  rm -f "${tmp_unit}"
}
trap cleanup EXIT

sed \
  -e "s|{{USER}}|${INSTALL_USER}|g" \
  -e "s|{{INSTALL_DIR}}|${INSTALL_DIR}|g" \
  "${SERVICE_TEMPLATE}" > "${tmp_unit}"

if [[ ! -f "${SERVICE_OUT}" ]] || ! cmp -s "${tmp_unit}" "${SERVICE_OUT}"; then
  install -m 0644 "${tmp_unit}" "${SERVICE_OUT}"
  systemctl daemon-reload
fi

echo "==> Restarting service"
systemctl restart "${SERVICE_NAME}"

echo
echo "==> Done"
echo "Service status: sudo systemctl status ${SERVICE_NAME} --no-pager"
echo "Logs: sudo journalctl -u ${SERVICE_NAME} -f"
