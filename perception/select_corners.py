import cv2
import numpy as np
from acquisition.camera_gige import GigECamera

points = []

def click_event(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Point {len(points)+1}: ({x}, {y})")
        points.append([x, y])
        cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
        cv2.imshow("Selecciona esquinas", frame)


camera = GigECamera()
camera.open()

frame = camera.read().copy()

cv2.imshow("Selecciona esquinas", frame)
cv2.setMouseCallback("Selecciona esquinas", click_event)

print("Haz click en las 4 esquinas de la cancha (orden horario)")
cv2.waitKey(0)

cv2.destroyAllWindows()
camera.release()

print("\nPuntos seleccionados:")
print(np.array(points))
