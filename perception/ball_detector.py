import cv2
import numpy as np


class BallDetector:
    def __init__(
        self,
        roi,
        lower_hsv,
        upper_hsv,
        min_area=80,
        max_area=3000,
        min_circularity=0.6,
        kernel_size=5,
    ):
        """
        roi: (x, y, w, h)
        lower_hsv, upper_hsv: np.array HSV
        """
        self.roi_x, self.roi_y, self.roi_w, self.roi_h = roi
        self.lower_hsv = lower_hsv
        self.upper_hsv = upper_hsv
        self.min_area = min_area
        self.max_area = max_area
        self.min_circularity = min_circularity
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def detect(self, frame):
        """
        Detecta la pelota en el frame.
        Retorna:
            dict con:
                found: bool
                x, y: coordenadas globales
                radius: radio
        """
        roi = frame[
            self.roi_y : self.roi_y + self.roi_h,
            self.roi_x : self.roi_x + self.roi_w,
        ]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

        # limpieza
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return {"found": False}

        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if not (self.min_area < area < self.max_area):
            return {"found": False}

        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            return {"found": False}

        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity < self.min_circularity:
            return {"found": False}

        (x, y), radius = cv2.minEnclosingCircle(c)

        cx_global = int(x + self.roi_x)
        cy_global = int(y + self.roi_y)

        return {
            "found": True,
            "x": cx_global,
            "y": cy_global,
            "radius": int(radius),
            "mask": mask,
        }
