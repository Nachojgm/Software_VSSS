#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

RUN_APP=0
CAMERA="mock"
PORT=""
SEND=0
SKIP_BRIDGE=0
SKIP_APT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run) RUN_APP=1; shift ;;
    --camera) CAMERA="${2:-mock}"; shift 2 ;;
    --port) PORT="${2:-}"; shift 2 ;;
    --send) SEND=1; shift ;;
    --skip-bridge) SKIP_BRIDGE=1; shift ;;
    --skip-apt) SKIP_APT=1; shift ;;
    *) echo "Argumento desconocido: $1"; exit 2 ;;
  esac
done

echo "Instalador VSSS Linux/Ubuntu"
echo "Carpeta: $ROOT_DIR"

install_apt_deps() {
  if ! command -v apt-get >/dev/null 2>&1; then
    echo "No se detecto apt-get. Instala manualmente python3, python3-venv, python3-tk, python3-pip, build-essential y g++."
    return
  fi

  echo "Instalando dependencias del sistema con apt..."
  if command -v sudo >/dev/null 2>&1; then
    SUDO=sudo
  else
    SUDO=""
  fi

  $SUDO apt-get update
  $SUDO apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-tk \
    build-essential \
    g++ \
    pkg-config
}

if [[ "$SKIP_APT" -eq 0 ]]; then
  if ! install_apt_deps; then
    echo "No se pudieron instalar dependencias apt. Continuo con lo disponible."
    echo "Puedes reintentar con permisos de administrador o usar --skip-apt."
  fi
fi

find_python() {
  for candidate in python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
      then
        echo "$candidate"
        return
      fi
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "No se encontro Python >= 3.10."
  exit 1
fi

echo "Python seleccionado: $PYTHON_BIN"

if [[ -d .venv ]]; then
  if ! .venv/bin/python - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
  then
    echo "Recreando .venv porque no usa Python >= 3.10"
    rm -rf .venv
  fi
fi

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

PY=".venv/bin/python"
"$PY" -m pip install --upgrade pip setuptools wheel
"$PY" -m pip install --upgrade --force-reinstall -r requirements.txt

if [[ "$SKIP_BRIDGE" -eq 0 ]]; then
  if [[ -x bridge/build/spinnaker_bridge ]]; then
    echo "Puente C++ Spinnaker ya compilado."
  else
    if bash bridge/build_bridge.sh; then
      echo "Puente C++ Spinnaker listo."
    else
      echo ""
      echo "No se pudo compilar el puente Spinnaker."
      echo "Instala Spinnaker SDK para Linux y revisa que libSpinnaker.so este disponible."
      echo "La app igual puede correr con --camera mock o --camera webcam."
    fi
  fi
fi

"$PY" check_env.py

echo ""
echo "Instalacion lista."
echo "Prueba sin hardware:"
echo "  bash run.sh --camera mock"
echo "Prueba GigE:"
echo "  bash run.sh --camera gige"
echo "Base station en Linux suele ser /dev/ttyUSB0 o /dev/ttyACM0."

if [[ "$RUN_APP" -eq 1 ]]; then
  args=(--camera "$CAMERA")
  [[ -n "$PORT" ]] && args+=(--port "$PORT")
  [[ "$SEND" -eq 1 ]] && args+=(--send)
  bash run.sh "${args[@]}"
fi
