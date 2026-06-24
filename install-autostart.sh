#!/usr/bin/env bash
# Install GNOME autostart entry with the correct install path.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.config/autostart/bidi-popup.desktop"

mkdir -p "${HOME}/.config/autostart"
sed "s|INSTALL_DIR|${DIR}|g" "${DIR}/bidi-popup.desktop" > "${DEST}"
chmod +x "${DIR}/start.sh"

echo "Installed autostart: ${DEST}"
