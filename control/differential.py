import math
from typing import Tuple

from config import ControlConfig


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def wrap_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class DifferentialController:
    def __init__(self, config: ControlConfig):
        self.config = config

    def stop(self) -> Tuple[int, int]:
        return 0, 0

    def go_to_pose(self, robot, target_xy) -> Tuple[int, int]:
        if robot is None or target_xy is None:
            return self.stop()

        dx = target_xy[0] - robot.x_m
        dy = target_xy[1] - robot.y_m
        distance = math.hypot(dx, dy)
        if distance < self.config.position_tolerance_m:
            return self.stop()

        target_heading = math.atan2(dy, dx)
        heading_error = wrap_angle(target_heading - robot.theta)
        angular = clamp(
            self.config.angle_kp * heading_error,
            -self.config.max_angular_rad_s,
            self.config.max_angular_rad_s,
        )

        heading_factor = clamp(
            1.0 - abs(heading_error) / self.config.heading_slowdown_rad,
            0.0,
            1.0,
        )
        linear = clamp(
            self.config.linear_kp * distance * heading_factor,
            -self.config.max_linear_m_s,
            self.config.max_linear_m_s,
        )

        return self.velocity_to_wheels(linear, angular)

    def velocity_to_wheels(self, linear_m_s, angular_rad_s) -> Tuple[int, int]:
        half_base = self.config.wheel_base_m / 2.0
        left_m_s = linear_m_s - angular_rad_s * half_base
        right_m_s = linear_m_s + angular_rad_s * half_base
        left = clamp(left_m_s * 1000.0, -self.config.max_wheel_mm_s, self.config.max_wheel_mm_s)
        right = clamp(right_m_s * 1000.0, -self.config.max_wheel_mm_s, self.config.max_wheel_mm_s)
        return int(left), int(right)
