#!/usr/bin/env bash
# Install systemd user service (reliable autostart on login).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.config/systemd/user/bidi-popup.service"

mkdir -p "${HOME}/.config/systemd/user"
sed "s|INSTALL_DIR|${DIR}|g" "${DIR}/bidi-popup.service" > "${DEST}"
chmod +x "${DIR}/start.sh"

systemctl --user daemon-reload
systemctl --user enable bidi-popup.service
systemctl --user restart bidi-popup.service

echo "Installed and started: bidi-popup.service"
systemctl --user status bidi-popup.service --no-pager || true
