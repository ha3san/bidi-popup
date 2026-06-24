#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer .venv (documented install); fall back to pyqt-env for local dev.
for VENV_DIR in ".venv" "pyqt-env"; do
  PYTHON="${DIR}/${VENV_DIR}/bin/python"
  if [[ -x "${PYTHON}" ]]; then
    break
  fi
done

LOCK_FILE="${XDG_RUNTIME_DIR:-/tmp}/bidi-popup.lock"

if [[ ! -x "${PYTHON:-}" ]]; then
  echo "bidi-popup: virtualenv not found in ${DIR}" >&2
  echo "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

exec flock -n "${LOCK_FILE}" "${PYTHON}" "${DIR}/listener.py"
