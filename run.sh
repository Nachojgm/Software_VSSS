#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -x .venv/bin/python ]]; then
  echo "No existe .venv. Instalando primero..."
  bash install.sh
fi

camera_arg=""
for ((i = 1; i <= $#; i++)); do
  if [[ "${!i}" == "--camera" ]]; then
    next=$((i + 1))
    if [[ $next -le $# ]]; then
      camera_arg="${!next}"
    fi
  fi
done

if [[ "$camera_arg" == "gige" || "$camera_arg" == "gige-bridge" ]]; then
  if [[ ! -x bridge/build/spinnaker_bridge || bridge/spinnaker_bridge.cpp -nt bridge/build/spinnaker_bridge || bridge/build_bridge.sh -nt bridge/build/spinnaker_bridge ]]; then
    echo "Compilando/actualizando puente C++ Spinnaker..."
    bash bridge/build_bridge.sh || true
  fi
fi

if [[ $# -eq 0 ]]; then
  exec .venv/bin/python main.py --camera mock
else
  exec .venv/bin/python main.py "$@"
fi
