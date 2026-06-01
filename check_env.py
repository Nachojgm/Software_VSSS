import argparse
import importlib.util
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

    pyspin = importlib.util.find_spec("PySpin") is not None
    print(f"PySpin/Spinnaker: {'OK' if pyspin else 'opcional, requerido solo para --camera gige'}")
    if args.require_gige and not pyspin:
        print("")
        print("ERROR: --camera gige requiere PySpin.")
        print("Instala FLIR Spinnaker SDK para Windows y habilita/instala el modulo Python PySpin.")
        print("Luego prueba:")
        print("  .\\.venv\\Scripts\\python.exe -c \"import PySpin; print('PySpin OK')\"")
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
