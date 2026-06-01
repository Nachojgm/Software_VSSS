import math
import time

import cv2
import numpy as np

from acquisition.camera_base import CameraBase


class MockCamera(CameraBase):
    """Synthetic field for UI and strategy tests without the GigE camera."""

    def __init__(self, width=960, height=720):
        self.width = width
        self.height = height
        self.started = False
        self.start_time = 0.0

    def open(self):
        self.started = True
        self.start_time = time.time()

    def read(self):
        if not self.started:
            return None

        t = time.time() - self.start_time
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (42, 118, 45)

        margin_x, margin_y = 90, 70
        cv2.rectangle(
            frame,
            (margin_x, margin_y),
            (self.width - margin_x, self.height - margin_y),
            (235, 235, 235),
            2,
        )
        cv2.line(
            frame,
            (self.width // 2, margin_y),
            (self.width // 2, self.height - margin_y),
            (220, 220, 220),
            1,
        )
        cv2.circle(frame, (self.width // 2, self.height // 2), 70, (220, 220, 220), 1)

        bx = int(self.width // 2 + math.cos(t * 0.8) * 190)
        by = int(self.height // 2 + math.sin(t * 1.1) * 120)
        cv2.circle(frame, (bx, by), 15, (0, 140, 255), -1)

        if hasattr(cv2, "aruco"):
            dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
            for marker_id in range(1, 6):
                if hasattr(cv2.aruco, "generateImageMarker"):
                    marker = cv2.aruco.generateImageMarker(dictionary, marker_id, 56)
                else:
                    marker = cv2.aruco.drawMarker(dictionary, marker_id, 56)
                x = 180 + (marker_id - 1) * 140
                y = 210 + int(math.sin(t + marker_id) * 80)
                patch = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
                frame[y : y + 56, x : x + 56] = patch
                cv2.circle(frame, (x + 28, y + 28), 38, (255, 90, 40), 2)

        return frame

    def release(self):
        self.started = False
