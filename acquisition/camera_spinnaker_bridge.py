import os
import subprocess
import sys
import threading

import numpy as np

from acquisition.camera_base import CameraBase


class SpinnakerBridgeCamera(CameraBase):
    """Reads frames from the C++ Spinnaker bridge executable."""

    def __init__(self, executable=None):
        self.executable = executable or self._default_executable()
        self.process = None
        self._stderr_thread = None
        self.last_error = ""

    def open(self):
        if not os.path.exists(self.executable):
            raise RuntimeError(
                "No se encontro el puente C++ de Spinnaker. En Windows ejecuta "
                ".\\install.ps1 o .\\bridge\\build_bridge.ps1. En Linux ejecuta "
                "bash install.sh o bash bridge/build_bridge.sh."
            )

        self.process = subprocess.Popen(
            [self.executable],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            bufsize=0,
        )
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stderr_thread.start()

    def read(self):
        if self.process is None or self.process.stdout is None:
            return None
        if self.process.poll() is not None:
            raise RuntimeError(f"El puente Spinnaker termino: {self.last_error}")

        header = self.process.stdout.readline()
        if not header:
            return None

        try:
            parts = header.decode("ascii").strip().split()
            if len(parts) != 4 or parts[0] != "VSSS_FRAME":
                self.last_error = header.decode("ascii", errors="replace").strip()
                return None
            width = int(parts[1])
            height = int(parts[2])
            byte_count = int(parts[3])
            payload = self.process.stdout.read(byte_count)
            self.process.stdout.read(1)  # trailing newline
            if len(payload) != byte_count:
                return None
            return np.frombuffer(payload, dtype=np.uint8).reshape((height, width, 3)).copy()
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def release(self):
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def _read_stderr(self):
        if self.process is None or self.process.stderr is None:
            return
        for line in self.process.stderr:
            self.last_error = line.decode("utf-8", errors="replace").strip()

    def _default_executable(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        name = "spinnaker_bridge.exe" if os.name == "nt" else "spinnaker_bridge"
        return os.path.join(root, "bridge", "build", name)
