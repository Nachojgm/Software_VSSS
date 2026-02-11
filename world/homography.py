import numpy as np
import cv2


class Homography:

    def __init__(self, image_points):

        real_width = 1.50
        real_height = 1.20

        real_points = np.array([
            [0.0, 0.0],
            [real_width, 0.0],
            [real_width, real_height],
            [0.0, real_height]
        ], dtype=np.float32)

        image_points = np.array(image_points, dtype=np.float32)

        self.H = cv2.getPerspectiveTransform(image_points, real_points)

    def transform(self, x, y):
        point = np.array([[[x, y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.H)
        return float(transformed[0][0][0]), float(transformed[0][0][1])
