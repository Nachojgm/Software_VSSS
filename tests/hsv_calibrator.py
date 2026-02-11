import cv2
import numpy as np
from acquisition.camera_gige import GigECamera

camera = GigECamera()
camera.open()

cv2.namedWindow("Trackbars")

# Trackbars HSV
cv2.createTrackbar("H_min", "Trackbars", 0, 179, lambda x: None)
cv2.createTrackbar("H_max", "Trackbars", 179, 179, lambda x: None)
cv2.createTrackbar("S_min", "Trackbars", 0, 255, lambda x: None)
cv2.createTrackbar("S_max", "Trackbars", 255, 255, lambda x: None)
cv2.createTrackbar("V_min", "Trackbars", 0, 255, lambda x: None)
cv2.createTrackbar("V_max", "Trackbars", 255, 255, lambda x: None)

while True:
    frame = camera.read()
    if frame is None:
        continue

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h_min = cv2.getTrackbarPos("H_min", "Trackbars")
    h_max = cv2.getTrackbarPos("H_max", "Trackbars")
    s_min = cv2.getTrackbarPos("S_min", "Trackbars")
    s_max = cv2.getTrackbarPos("S_max", "Trackbars")
    v_min = cv2.getTrackbarPos("V_min", "Trackbars")
    v_max = cv2.getTrackbarPos("V_max", "Trackbars")

    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    mask = cv2.inRange(hsv, lower, upper)

    cv2.imshow("Original", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(1) == 27:
        break

camera.release()
cv2.destroyAllWindows()
