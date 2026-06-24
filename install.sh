#!/usr/bin/env bash
# Install Bidi Popup into the current directory (.venv + dependencies).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "bidi-popup: python3 is required" >&2
  echo "  sudo apt install python3 python3-venv python3-pip" >&2
  exit 1
fi

echo "==> Creating virtualenv in ${DIR}/.venv"
python3 -m venv .venv

echo "==> Installing Python dependencies"
.venv/bin/pip install -U pip wheel
.venv/bin/pip install -r requirements.txt

chmod +x start.sh install-autostart.sh install-shortcut.sh install-service.sh listener.py

SESSION="${XDG_SESSION_TYPE:-unknown}"
echo ""
echo "==> Done."
echo "    Run:              ./start.sh"
echo "    Autostart:        ./install-autostart.sh"
if [[ "${SESSION}" == "wayland" ]]; then
  echo "    Wayland shortcut: ./install-shortcut.sh"
fi
echo ""
echo "System packages (if missing):"
echo "  sudo apt install xclip wl-clipboard fonts-vazirmatn"
