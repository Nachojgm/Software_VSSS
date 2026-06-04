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
    project_dir = os.path.dirname(__file__)
    bridge_name = "spinnaker_bridge.exe" if os.name == "nt" else "spinnaker_bridge"
    bridge_path = os.path.join(project_dir, "bridge", "build", bridge_name)
    bridge_source = os.path.join(project_dir, "bridge", "spinnaker_bridge.cpp")
    bridge_script = os.path.join(project_dir, "bridge", "build_bridge.ps1" if os.name == "nt" else "build_bridge.sh")
    bridge_ok = os.path.exists(bridge_path)
    bridge_stale = (
        bridge_ok
        and (
            (os.path.exists(bridge_source) and os.path.getmtime(bridge_source) > os.path.getmtime(bridge_path))
            or (os.path.exists(bridge_script) and os.path.getmtime(bridge_script) > os.path.getmtime(bridge_path))
        )
    )
    if bridge_stale:
        bridge_status = "DESACTUALIZADO - recompila el bridge"
    elif bridge_ok:
        bridge_status = "OK"
    else:
        bridge_status = "NO COMPILADO - fallback para --camera gige"
    print(f"Bridge C++ Spinnaker: {bridge_status}")
    if args.require_gige and not pyspin_ok:
        if bridge_ok and not bridge_stale:
            print("PySpin no esta disponible, pero el bridge C++ esta listo para --camera gige.")
        else:
            print("")
            print("ERROR: --camera gige requiere PySpin oficial o el bridge C++ Spinnaker compilado y actualizado.")
            if os.name == "nt":
                print("Para el bridge C++ instala Spinnaker SDK y Visual Studio Build Tools con C++.")
                print("Luego ejecuta:")
                print("  .\\bridge\\build_bridge.ps1")
            else:
                print("Para el bridge C++ instala Spinnaker SDK para Linux y g++.")
                print("Luego ejecuta:")
                print("  bash bridge/build_bridge.sh")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
