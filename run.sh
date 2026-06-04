#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -x .venv/bin/python ]]; then
  echo "No existe .venv. Instalando primero..."
  bash install.sh
fi

if [[ $# -eq 0 ]]; then
  exec .venv/bin/python main.py --camera mock
else
  exec .venv/bin/python main.py "$@"
fi
