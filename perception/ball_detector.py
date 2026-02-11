import cv2
import numpy as np


class BallDetector:
    def __init__(self, lower_hsv, upper_hsv, min_area=500):
        self.lower_hsv = lower_hsv
        self.upper_hsv = upper_hsv
        self.min_area = min_area

    def detect(self, frame):

        if frame is None:
            return {"found": False}

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

        # Pequeña limpieza
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return {"found": False, "mask": mask}

        # Contorno más grande
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        #print("Area:", area)

        if area < self.min_area:
            return {"found": False, "mask": mask}

        (x, y), radius = cv2.minEnclosingCircle(c)

        return {
            "found": True,
            "x": int(x),
            "y": int(y),
            "radius": int(radius),
            "mask": mask
        }
