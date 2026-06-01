import importlib.util
import platform
import sys


REQUIRED = [
    ("cv2", "opencv-contrib-python"),
    ("numpy", "numpy"),
    ("serial", "pyserial"),
]


def main():
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

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
