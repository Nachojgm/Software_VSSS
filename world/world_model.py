import math
import time

from world.entities import Ball, Robot, WorldState
from world.kalman import AngleTracker, ConstantVelocityKalman2D


class WorldModel:

    def __init__(self):
        self.ball_position = None
        self.ball_velocity = (0.0, 0.0)
        self.last_time = None
        self.last_position = None
        self.robots = []
        self.ball = None
        self.ball_filter = ConstantVelocityKalman2D(process_noise=0.8, measurement_noise=0.015)
        self.robot_filters = {}
        self.robot_angle_filters = {}

    def update_ball(self, x, y, radius=0.0):

        current_time = time.time()

        if self.last_position is not None:
            dt = current_time - self.last_time

            if dt > 0:
                vx = (x - self.last_position[0]) / dt
                vy = (y - self.last_position[1]) / dt
                self.ball_velocity = (vx, vy)

        self.ball_position = (x, y)
        self.ball = Ball(x, y, x, y, radius)
        self.last_position = (x, y)
        self.last_time = current_time

    def update(self, ball, robots):
        current_time = time.time()
        dt = 1.0 / 30.0 if self.last_time is None else current_time - self.last_time

        if ball is not None:
            x_m, y_m, vx_m_s, vy_m_s = self.ball_filter.update(ball.x_m, ball.y_m, dt)
            self.ball = Ball(
                x_px=ball.x_px,
                y_px=ball.y_px,
                x_m=x_m,
                y_m=y_m,
                radius_px=ball.radius_px,
                vx_m_s=vx_m_s,
                vy_m_s=vy_m_s,
            )
            self.ball_velocity = (vx_m_s, vy_m_s)
        else:
            self.ball = None
            self.ball_velocity = (0.0, 0.0)

        filtered_robots = []
        seen_robot_ids = set()
        for robot in robots:
            seen_robot_ids.add(robot.robot_id)
            tracker = self.robot_filters.setdefault(
                robot.robot_id,
                ConstantVelocityKalman2D(process_noise=0.35, measurement_noise=0.01),
            )
            angle_tracker = self.robot_angle_filters.setdefault(robot.robot_id, AngleTracker())
            x_m, y_m, vx_m_s, vy_m_s = tracker.update(robot.x_m, robot.y_m, dt)
            theta, omega = angle_tracker.update(robot.theta, dt)
            filtered_robots.append(
                Robot(
                    marker_id=robot.marker_id,
                    robot_id=robot.robot_id,
                    x_px=robot.x_px,
                    y_px=robot.y_px,
                    x_m=x_m,
                    y_m=y_m,
                    theta=theta,
                    vx_m_s=vx_m_s,
                    vy_m_s=vy_m_s,
                    angular_velocity_rad_s=omega,
                )
            )

        self.robots = filtered_robots
        for robot_id in list(self.robot_filters.keys()):
            if robot_id not in seen_robot_ids:
                self.robot_filters.pop(robot_id, None)
                self.robot_angle_filters.pop(robot_id, None)
        self.last_time = current_time

    def state(self):
        return WorldState(
            ball=self.ball,
            robots=tuple(self.robots),
            ball_velocity_m_s=self.ball_velocity,
        )

    def get_ball_speed(self):
        vx, vy = self.ball_velocity
        return math.sqrt(vx**2 + vy**2)
