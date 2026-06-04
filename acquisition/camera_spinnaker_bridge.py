import os
import queue
import base64
import subprocess
import sys
import threading
import time

import numpy as np

from acquisition.camera_base import CameraBase


class SpinnakerBridgeCamera(CameraBase):
    """Reads frames from the C++ Spinnaker bridge executable."""

    def __init__(self, executable=None):
        self.executable = executable or self._default_executable()
        self.process = None
        self._stdout_thread = None
        self._stderr_thread = None
        self._frame_queue = queue.Queue(maxsize=1)
        self._closing = False
        self.last_status = ""
        self.last_error = ""

    def open(self):
        if not os.path.exists(self.executable):
            raise RuntimeError(
                "No se encontro el puente C++ de Spinnaker. En Windows ejecuta "
                ".\\install.ps1 o .\\bridge\\build_bridge.ps1. En Linux ejecuta "
                "bash install.sh o bash bridge/build_bridge.sh."
            )

        print(f"Usando puente Spinnaker: {self.executable}")
        self._closing = False
        self.process = subprocess.Popen(
            [self.executable],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            bufsize=0,
        )
        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()
        time.sleep(0.2)
        if self.process.poll() is not None:
            raise RuntimeError(f"El puente Spinnaker no pudo iniciar: {self.last_error}")

    def read(self):
        process = self.process
        if process is None or process.stdout is None:
            return None
        if process.poll() is not None:
            detail = self.last_error or self.last_status or "sin detalle"
            raise RuntimeError(f"El puente Spinnaker termino: {detail}")

        try:
            return self._frame_queue.get_nowait()
        except queue.Empty:
            return None

    def _read_stdout(self):
        process = self.process
        if process is None or process.stdout is None:
            return
        stdout = process.stdout
        while not self._closing and process.poll() is None:
            frame = self._read_frame_from_stdout(stdout)
            if frame is None:
                continue
            while self._frame_queue.full():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self._frame_queue.put(frame)

    def _read_frame_from_stdout(self, stdout):
        header = stdout.readline()
        if not header:
            return None
        try:
            parts = header.decode("ascii").strip().split()
            if len(parts) == 5 and parts[0] == "VSSS_FRAME_B64":
                width = int(parts[1])
                height = int(parts[2])
                byte_count = int(parts[3])
                payload_size = int(parts[4])
                payload = self._read_exact(stdout, payload_size)
                newline = self._read_exact(stdout, 1)
                if payload is None or newline != b"\n":
                    return None
                raw = base64.b64decode(payload, validate=True)
                if len(raw) != byte_count:
                    self.last_error = f"Frame incompleto: {len(raw)}/{byte_count} bytes"
                    return None
                return np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3)).copy()

            if len(parts) != 4 or parts[0] != "VSSS_FRAME":
                self.last_error = header.decode("ascii", errors="replace").strip()
                return None
            width = int(parts[1])
            height = int(parts[2])
            byte_count = int(parts[3])
            payload = self._read_exact(stdout, byte_count)
            newline = self._read_exact(stdout, 1)
            if payload is None or newline != b"\n":
                return None
            return np.frombuffer(payload, dtype=np.uint8).reshape((height, width, 3)).copy()
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def _read_exact(self, stream, byte_count):
        chunks = []
        remaining = byte_count
        while remaining > 0 and not self._closing:
            chunk = stream.read(remaining)
            if not chunk:
                return None
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def release(self):
        self._closing = True
        process = self.process
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        self.process = None

    def _read_stderr(self):
        process = self.process
        if process is None or process.stderr is None:
            return
        for line in process.stderr:
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            self.last_status = text
            lowered = text.lower()
            if any(word in lowered for word in ("error", "fallo", "no se", "exception")):
                self.last_error = text
            print(f"[spinnaker-bridge] {text}", file=sys.stderr)

    def _default_executable(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        name = "spinnaker_bridge.exe" if os.name == "nt" else "spinnaker_bridge"
        return os.path.join(root, "bridge", "build", name)
