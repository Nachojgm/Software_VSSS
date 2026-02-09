import cv2
import numpy as np
from perception.ball_detector import BallDetector

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

detector = BallDetector(
    roi=(80, 40, 1120, 640),
    lower_hsv=np.array([21, 9, 234]),
    upper_hsv=np.array([37, 255, 255]),
)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = detector.detect(frame)

    if result["found"]:
        cv2.circle(
            frame,
            (result["x"], result["y"]),
            result["radius"],
            (0, 255, 0),
            2,
        )
        cv2.circle(frame, (result["x"], result["y"]), 3, (0, 0, 255), -1)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", result.get("mask", frame))

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
