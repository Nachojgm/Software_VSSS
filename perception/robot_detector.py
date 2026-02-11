import cv2
import numpy as np


class RobotDetector:

    def __init__(self):

        self.dictionary = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_ARUCO_ORIGINAL
        )

        self.parameters = cv2.aruco.DetectorParameters()

        self.detector = cv2.aruco.ArucoDetector(
            self.dictionary,
            self.parameters
        )

    def detect(self, frame):

        corners, ids, _ = self.detector.detectMarkers(frame)

        robots = []

        if ids is None:
            return robots

        for i in range(len(ids)):

            marker_id = int(ids[i][0])
            marker_corners = corners[i][0]

            # Centro
            center_x = np.mean(marker_corners[:, 0])
            center_y = np.mean(marker_corners[:, 1])

            # Orientación
            top_left = marker_corners[0]
            top_right = marker_corners[1]

            dx = top_right[0] - top_left[0]
            dy = top_right[1] - top_left[1]

            angle = np.arctan2(dy, dx)

            robots.append({
                "id": marker_id,
                "x": float(center_x),
                "y": float(center_y),
                "theta": float(angle)
            })

        return robots
