import cv2
import numpy as np
import time

from acquisition.camera_gige import GigECamera
from perception.ball_detector import BallDetector
from world.homography import Homography
from world.world_model import WorldModel
from perception.robot_detector import RobotDetector

robot_detector = RobotDetector()
world = WorldModel()
camera = GigECamera()
camera.open()

detector = BallDetector(
    lower_hsv=np.array([6, 80, 100]),
    upper_hsv=np.array([30, 255, 255]),
    min_area=250
)
image_points = [
    [186, 134],
    [964, 116],
    [983, 709],
    [177, 725]
]

homography = Homography(image_points)

print("ESC para salir")

while True:
    frame = camera.read()
    if frame is None:
        continue
    
    robots = robot_detector.detect(frame)

    for robot in robots:
        x = int(robot["x"])
        y = int(robot["y"])
        theta = robot["theta"]

        cv2.circle(frame, (x, y), 10, (255, 0, 0), -1)

        # Dibujar dirección
        length = 40
        end_x = int(x + length * np.cos(theta))
        end_y = int(y + length * np.sin(theta))

        cv2.line(frame, (x, y), (end_x, end_y), (0, 255, 0), 3)

        print("Robot ID:", robot["id"], "Theta:", theta)
    robots = robot_detector.detect(frame)

    for robot in robots:
        x = int(robot["x"])
        y = int(robot["y"])
        theta = robot["theta"]

        cv2.circle(frame, (x, y), 10, (255, 0, 0), -1)

        # Dibujar dirección
        length = 40
        end_x = int(x + length * np.cos(theta))
        end_y = int(y + length * np.sin(theta))

        cv2.line(frame, (x, y), (end_x, end_y), (0, 255, 0), 3)

        print("Robot ID:", robot["id"], "Theta:", theta)

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
    x_m, y_m = homography.transform(global_x, global_y)
    world.update_ball(x_m, y_m)
    #print("Ball (m):", x_m, y_m)
    #print("Velocity (m/s):", world.ball_velocity)
    #print("Speed:", world.get_ball_speed())



    cv2.rectangle(frame,
              (x_min, y_min),
              (x_max, y_max),
              (255, 0, 0), 2)

    cv2.imshow("GigE", frame)
    cv2.imshow("Mask", result["mask"])

    if cv2.waitKey(1) == 27:
        break

    time.sleep(0.05)

camera.release()
cv2.destroyAllWindows()
