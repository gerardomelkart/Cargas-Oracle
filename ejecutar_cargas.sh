#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv --system-site-packages .venv
fi

if ! .venv/bin/python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('oracledb') or importlib.util.find_spec('cx_Oracle') else 1)"; then
    .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python cargar_oracle.py "$@"
