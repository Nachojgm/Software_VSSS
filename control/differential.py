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

    def go_to_pose(
        self,
        robot,
        target_xy,
        final_heading=None,
        allow_fast_turn=False,
    ) -> Tuple[int, int]:
        if robot is None or target_xy is None:
            return self.stop()

        dx = target_xy[0] - robot.x_m
        dy = target_xy[1] - robot.y_m
        distance = math.hypot(dx, dy)
        if distance < self.config.position_tolerance_m:
            if final_heading is not None:
                final_error = wrap_angle(final_heading - robot.theta)
                if abs(final_error) > self.config.final_heading_tolerance_rad:
                    return self.turn_in_place(final_error, allow_fast_turn)
            return self.stop()

        target_heading = math.atan2(dy, dx)
        heading_error = wrap_angle(target_heading - robot.theta)
        angular_limit = (
            self.config.kick_max_angular_rad_s
            if allow_fast_turn
            else self.config.max_angular_rad_s
        )
        angle_kp = self.config.kick_angle_kp if allow_fast_turn else self.config.angle_kp
        angular = clamp(
            angle_kp * heading_error,
            -angular_limit,
            angular_limit,
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

    def turn_in_place(self, heading_error, allow_fast_turn=False) -> Tuple[int, int]:
        angular_limit = (
            self.config.kick_max_angular_rad_s
            if allow_fast_turn
            else self.config.max_angular_rad_s
        )
        angle_kp = self.config.kick_angle_kp if allow_fast_turn else self.config.angle_kp
        angular = clamp(angle_kp * heading_error, -angular_limit, angular_limit)
        return self.velocity_to_wheels(0.0, angular)

    def velocity_to_wheels(self, linear_m_s, angular_rad_s) -> Tuple[int, int]:
        half_base = self.config.wheel_base_m / 2.0
        left_m_s = linear_m_s - angular_rad_s * half_base
        right_m_s = linear_m_s + angular_rad_s * half_base
        left = clamp(left_m_s * 1000.0, -self.config.max_wheel_mm_s, self.config.max_wheel_mm_s)
        right = clamp(right_m_s * 1000.0, -self.config.max_wheel_mm_s, self.config.max_wheel_mm_s)
        return int(left), int(right)
