from typing import List, Optional, Tuple

from config import AppConfig, NUM_ROBOTS
from perception.ball_detector import BallDetector
from perception.robot_detector import RobotDetector
from world.entities import Ball, Robot
from world.homography import Homography


class PerceptionPipeline:
    def __init__(self, config: AppConfig):
        self.config = config
        self.ball_detector = BallDetector(
            config.vision.ball_lower_hsv,
            config.vision.ball_upper_hsv,
            config.vision.ball_min_area_px,
        )
        self.robot_detector = RobotDetector(config.vision.aruco_dictionary)
        self.homography: Optional[Homography] = None
        self.last_ball_mask = None
        self.dynamic_marker_to_robot = {}

    def set_field_corners(self, image_points: List[Tuple[float, float]]):
        if len(image_points) != 4:
            raise ValueError("Se requieren 4 esquinas: superior izq, superior der, inferior der, inferior izq")
        self.homography = Homography(
            image_points,
            real_width=self.config.field.length_m,
            real_height=self.config.field.width_m,
        )

    def process(self, frame):
        ball = self._detect_ball(frame)
        robots = self._detect_robots(frame)
        return ball, robots

    def _to_world(self, x, y):
        if self.homography is None:
            return float(x), float(y)
        return self.homography.transform(x, y)

    def _detect_ball(self, frame):
        result = self.ball_detector.detect(frame)
        self.last_ball_mask = result.get("mask")
        if not result.get("found"):
            return None
        x_m, y_m = self._to_world(result["x"], result["y"])
        return Ball(
            x_px=result["x"],
            y_px=result["y"],
            x_m=x_m,
            y_m=y_m,
            radius_px=result.get("radius", 0),
        )

    def _detect_robots(self, frame):
        detections = self.robot_detector.detect(frame)
        robots = []
        for detected in detections:
            marker_id = detected["id"]
            robot_id = self._robot_id_for_marker(marker_id)
            x_m, y_m = self._to_world(detected["x"], detected["y"])
            robots.append(
                Robot(
                    marker_id=marker_id,
                    robot_id=robot_id,
                    x_px=detected["x"],
                    y_px=detected["y"],
                    x_m=x_m,
                    y_m=y_m,
                    theta=detected["theta"],
                )
            )
        return robots

    def _robot_id_for_marker(self, marker_id):
        configured = self.config.team.marker_to_robot.get(marker_id)
        if configured is not None:
            return configured

        assigned = self.dynamic_marker_to_robot.get(marker_id)
        if assigned is not None:
            return assigned

        used_slots = set(self.config.team.marker_to_robot.values())
        used_slots.update(self.dynamic_marker_to_robot.values())
        for robot_id in range(1, NUM_ROBOTS + 1):
            if robot_id not in used_slots:
                self.dynamic_marker_to_robot[marker_id] = robot_id
                return robot_id

        return marker_id
