from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Ball:
    x_px: float
    y_px: float
    x_m: float
    y_m: float
    radius_px: float = 0.0
    vx_m_s: float = 0.0
    vy_m_s: float = 0.0


@dataclass
class Robot:
    marker_id: int
    robot_id: int
    x_px: float
    y_px: float
    x_m: float
    y_m: float
    theta: float
    vx_m_s: float = 0.0
    vy_m_s: float = 0.0
    angular_velocity_rad_s: float = 0.0


@dataclass
class WorldState:
    ball: Optional[Ball]
    robots: Tuple[Robot, ...]
    ball_velocity_m_s: Tuple[float, float] = (0.0, 0.0)
