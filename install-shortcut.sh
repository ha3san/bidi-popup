#!/usr/bin/env bash
# Register Ctrl+Alt+Space in GNOME to trigger Bidi Popup (required on Wayland).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTRY="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/bidi-popup/"
BASE="org.gnome.settings-daemon.plugins.media-keys"
PREFIX="${BASE}.custom-keybinding:${ENTRY}"

if ! command -v gsettings >/dev/null 2>&1; then
  echo "gsettings not found — this script is for GNOME." >&2
  echo "Bind your desktop shortcut to: ${DIR}/start.sh trigger" >&2
  exit 1
fi

chmod +x "${DIR}/start.sh"

python3 - "${ENTRY}" "${DIR}/start.sh trigger" <<'PY'
import ast
import subprocess
import sys

entry, command = sys.argv[1:3]
base = "org.gnome.settings-daemon.plugins.media-keys"
prefix = f"{base}.custom-keybinding:{entry}"

raw = subprocess.check_output(["gsettings", "get", base, "custom-keybindings"], text=True).strip()
if raw in ("@as []", "[]"):
    items: list[str] = []
else:
    items = ast.literal_eval(raw.removeprefix("@as ").strip())

if entry not in items:
    items.append(entry)

formatted = "[" + ", ".join(f"'{item}'" for item in items) + "]"
subprocess.run(["gsettings", "set", base, "custom-keybindings", formatted], check=True)

for key, value in (
    ("name", "Bidi Popup"),
    ("command", command),
    ("binding", "<Primary><Alt>space"),
):
    subprocess.run(["gsettings", "set", prefix, key, value], check=True)

print(f"GNOME shortcut installed: Ctrl+Alt+Space -> {command}")
PY

echo "Make sure Bidi Popup is running: ${DIR}/start.sh"
