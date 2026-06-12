#!/usr/bin/env bash
# Sync .akemi/agents/claude/ artifacts into .claude/ directory.
# Thin wrapper - delegates to Python for all heavy lifting.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AKEMI_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$AKEMI_DIR/.venv"

find_venv_python() {
  local c
  for c in "$VENV_DIR/bin/python" "$VENV_DIR/Scripts/python.exe"; do
    [[ -x "$c" ]] && { echo "$c"; return 0; }
  done
  return 1
}

if ! PYTHON="$(find_venv_python)"; then
  echo "Setting up Akemi Python environment..."
  BOOT_PYTHON="$(command -v python3 || command -v python || command -v py)" \
    || { echo "ERROR: no Python interpreter found (need python3 >= 3.10)" >&2; exit 1; }
  "$BOOT_PYTHON" -m venv "$VENV_DIR"
  PYTHON="$(find_venv_python)"
  "$PYTHON" -m pip install --quiet --upgrade pip
  "$PYTHON" -m pip install --quiet "$AKEMI_DIR/python/"
fi

exec "$PYTHON" -m akemi sync-claude "$@"
