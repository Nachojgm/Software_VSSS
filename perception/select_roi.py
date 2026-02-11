import cv2
from acquisition.camera_gige import GigECamera

camera = GigECamera()
camera.open()

print("Selecciona la cancha y presiona ENTER")

frame = camera.read()

if frame is None:
    print("No se pudo leer frame")
    exit()

frame = frame.copy()

# Selector interactivo
roi = cv2.selectROI("Selecciona la cancha", frame, showCrosshair=True)

x, y, w, h = roi

print("\n=== ROI SELECCIONADO ===")
print("x_min =", x)
print("x_max =", x + w)
print("y_min =", y)
print("y_max =", y + h)

cv2.destroyAllWindows()
camera.release()
