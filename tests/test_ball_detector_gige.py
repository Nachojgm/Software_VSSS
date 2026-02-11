import cv2
import numpy as np
import time

from acquisition.camera_gige import GigECamera
from perception.ball_detector import BallDetector


camera = GigECamera()
camera.open()

detector = BallDetector(
    lower_hsv=np.array([6, 80, 100]),
    upper_hsv=np.array([30, 255, 255]),
    min_area=250
)

print("ESC para salir")

while True:
    frame = camera.read()
    if frame is None:
        continue

    # === ROI de la cancha ===
    x_min, x_max = 119, 1022
    y_min, y_max = 75, 756

    roi = frame[y_min:y_max, x_min:x_max]

    result = detector.detect(roi)

    #print("FOUND:", result["found"])

    if result["found"]:
        global_x = result["x"] + x_min
        global_y = result["y"] + y_min

        cv2.circle(frame, (global_x, global_y),
                result["radius"],
                (0, 255, 0), 3)


    cv2.rectangle(frame,
              (x_min, y_min),
              (x_max, y_max),
              (255, 0, 0), 2)

    cv2.imshow("GigE", frame)
    cv2.imshow("Mask", result["mask"])

    if cv2.waitKey(1) == 27:
        break

    time.sleep(0.005)

camera.release()
cv2.destroyAllWindows()
