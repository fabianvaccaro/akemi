#!/usr/bin/env bash
# Rebuild .akemi/graph/index.yaml from all node files.
# Thin wrapper - delegates to Python for all heavy lifting.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AKEMI_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$AKEMI_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"

if [[ ! -f "$PYTHON" ]]; then
  echo "Setting up Akemi Python environment..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet "$AKEMI_DIR/python/"
fi

exec "$PYTHON" -m akemi rebuild-index "$@"
