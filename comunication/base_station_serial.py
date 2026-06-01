import threading
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from config import NUM_ROBOTS

try:
    import serial
except ImportError:
    serial = None


WheelCommand = Tuple[int, int]


@dataclass
class SerialStatus:
    connected: bool = False
    port: str = ""
    last_line: str = ""
    last_error: str = ""


class BaseStationSerial:
    """Sends L1,R1,...,L5,R5 lines expected by the ESP-NOW base station."""

    def __init__(self, port: str, baudrate: int = 115200, max_wheel_mm_s: int = 1500):
        self.port = port
        self.baudrate = baudrate
        self.max_wheel_mm_s = max_wheel_mm_s
        self._serial = None
        self._lock = threading.Lock()
        self.status = SerialStatus(port=port)

    def open(self):
        if not self.port:
            self.status.last_error = "Puerto serial no configurado"
            return False
        if serial is None:
            self.status.last_error = "pyserial no esta instalado"
            return False

        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0)
            self.status.connected = True
            self.status.last_error = ""
            return True
        except Exception as exc:
            self.status.connected = False
            self.status.last_error = str(exc)
            return False

    def close(self):
        with self._lock:
            if self._serial is not None:
                self._serial.close()
                self._serial = None
        self.status.connected = False

    def send(self, commands: Iterable[WheelCommand]):
        values: List[int] = []
        for left, right in list(commands)[:NUM_ROBOTS]:
            values.append(self._clamp(left))
            values.append(self._clamp(right))
        while len(values) < NUM_ROBOTS * 2:
            values.extend([0, 0])

        line = ",".join(str(v) for v in values) + "\n"
        self.status.last_line = line.strip()

        with self._lock:
            if self._serial is None:
                return False
            try:
                self._serial.write(line.encode("ascii"))
                return True
            except Exception as exc:
                self.status.last_error = str(exc)
                self.status.connected = False
                return False

    def stop_all(self):
        return self.send([(0, 0)] * NUM_ROBOTS)

    def _clamp(self, value):
        value = int(round(value))
        return max(-self.max_wheel_mm_s, min(self.max_wheel_mm_s, value))


class CommandStreamer:
    def __init__(self, transport: Optional[BaseStationSerial], hz: float = 20.0):
        self.transport = transport
        self.period_s = 1.0 / hz
        self.commands: List[WheelCommand] = [(0, 0)] * NUM_ROBOTS
        self.enabled = False
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self.transport is not None:
            self.transport.stop_all()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def set_commands(self, commands: Iterable[WheelCommand]):
        with self._lock:
            self.commands = list(commands)[:NUM_ROBOTS]
            while len(self.commands) < NUM_ROBOTS:
                self.commands.append((0, 0))

    def _loop(self):
        while self._running:
            with self._lock:
                commands = list(self.commands) if self.enabled else [(0, 0)] * NUM_ROBOTS
            if self.transport is not None:
                self.transport.send(commands)
            time.sleep(self.period_s)
