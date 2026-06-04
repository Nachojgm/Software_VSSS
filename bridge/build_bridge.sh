#!/usr/bin/env bash
set -euo pipefail

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$BRIDGE_DIR/build"
SOURCE="$BRIDGE_DIR/spinnaker_bridge.cpp"
OUTPUT="$BUILD_DIR/spinnaker_bridge"
SPINNAKER_ROOT="${SPINNAKER_ROOT:-}"

find_spinnaker_root() {
  if [[ -n "$SPINNAKER_ROOT" && -f "$SPINNAKER_ROOT/include/Spinnaker.h" ]]; then
    echo "$SPINNAKER_ROOT"
    return
  fi

  for candidate in \
    /opt/spinnaker \
    /usr/local/spinnaker \
    /usr/local \
    /usr; do
    if [[ -f "$candidate/include/Spinnaker.h" || -f "$candidate/include/spinnaker/Spinnaker.h" ]]; then
      echo "$candidate"
      return
    fi
  done

  return 1
}

ROOT="$(find_spinnaker_root || true)"
if [[ -z "$ROOT" ]]; then
  echo "No se encontro Spinnaker SDK Linux."
  echo "Instala el SDK o ejecuta con SPINNAKER_ROOT=/ruta/spinnaker bash bridge/build_bridge.sh"
  exit 1
fi

INCLUDE_FLAGS=()
if [[ -f "$ROOT/include/Spinnaker.h" ]]; then
  INCLUDE_FLAGS+=("-I$ROOT/include")
fi
if [[ -f "$ROOT/include/spinnaker/Spinnaker.h" ]]; then
  INCLUDE_FLAGS+=("-I$ROOT/include/spinnaker")
fi

LIB_FLAGS=()
for libdir in "$ROOT/lib" "$ROOT/lib64" /usr/lib /usr/local/lib /usr/lib/x86_64-linux-gnu; do
  if [[ -d "$libdir" ]]; then
    if compgen -G "$libdir/libSpinnaker.so*" >/dev/null; then
      LIB_FLAGS+=("-L$libdir" "-Wl,-rpath,$libdir")
      break
    fi
  fi
done

if [[ "${#LIB_FLAGS[@]}" -eq 0 ]]; then
  echo "No se encontro libSpinnaker.so."
  exit 1
fi

mkdir -p "$BUILD_DIR"

echo "Compilando puente Spinnaker Linux"
echo "SDK: $ROOT"
g++ -std=c++17 -O2 "${INCLUDE_FLAGS[@]}" "$SOURCE" "${LIB_FLAGS[@]}" -lSpinnaker -o "$OUTPUT"
chmod +x "$OUTPUT"
echo "Bridge listo: $OUTPUT"
