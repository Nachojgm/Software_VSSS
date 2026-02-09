from acquisition.camera_gige import GigECamera
from perception.ball_detector import BallDetector
import numpy as np
import cv2
import time

camera = GigECamera()
camera.open()

detector = BallDetector(
    roi=(0, 0, 1920, 1080),
    lower_hsv=np.array([21, 9, 234]),
    upper_hsv=np.array([37, 255, 255]),
)

while True:
   #print("Leyendo frame")
    frame = camera.read()
   #print("Frame listo")
    if frame is None:
        continue

    result = detector.detect(frame)

    if result["found"]:
        cv2.circle(frame, (result["x"], result["y"]), result["radius"], (0, 255, 0), 2)

    cv2.imshow("GigE", frame)
    key = cv2.waitKey(1)
    if key == 27:  # ESC
        break
    time.sleep(0.005)  # 5 ms
camera.release()
cv2.destroyAllWindows()
