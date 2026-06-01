import argparse
import importlib
import importlib.util
import os
import platform
import sys


REQUIRED = [
    ("cv2", "opencv-contrib-python"),
    ("numpy", "numpy"),
    ("serial", "pyserial"),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Revisa dependencias del software VSSS.")
    parser.add_argument(
        "--require-gige",
        action="store_true",
        help="Falla si PySpin/Spinnaker no esta disponible.",
    )
    return parser.parse_args()


def validate_pyspin():
    if importlib.util.find_spec("PySpin") is None:
        return False, "NO INSTALADO"

    try:
        pyspin = importlib.import_module("PySpin")
    except Exception as exc:
        return False, f"NO IMPORTA ({exc})"

    if not hasattr(pyspin, "System"):
        path = getattr(pyspin, "__file__", "ruta desconocida")
        return False, f"MODULO INCORRECTO ({path})"

    return True, "OK"


def main():
    args = parse_args()
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print("")

    ok = True
    if sys.version_info < (3, 10):
        print("ERROR: Se requiere Python 3.10 o superior.")
        ok = False

    for module_name, package_name in REQUIRED:
        found = importlib.util.find_spec(module_name) is not None
        print(f"{package_name}: {'OK' if found else 'NO INSTALADO'}")
        ok = ok and found

    pyspin_ok, pyspin_status = validate_pyspin()
    print(f"PySpin/Spinnaker: {pyspin_status if pyspin_ok else pyspin_status + ' - requerido solo para --camera gige'}")
    bridge_path = os.path.join(os.path.dirname(__file__), "bridge", "build", "spinnaker_bridge.exe")
    bridge_ok = os.path.exists(bridge_path)
    print(f"Bridge C++ Spinnaker: {'OK' if bridge_ok else 'NO COMPILADO - fallback para --camera gige'}")
    if args.require_gige and not pyspin_ok:
        if bridge_ok:
            print("PySpin no esta disponible, pero el bridge C++ esta listo para --camera gige.")
        else:
            print("")
            print("ERROR: --camera gige requiere PySpin oficial o el bridge C++ Spinnaker compilado.")
            print("Para el bridge C++ instala Spinnaker SDK y Visual Studio Build Tools con C++.")
            print("Luego ejecuta:")
            print("  .\\bridge\\build_bridge.ps1")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
