from dataclasses import dataclass, field as dataclass_field
from typing import Dict, Tuple


NUM_ROBOTS = 5


@dataclass
class FieldConfig:
    # Centralized because tournament dimensions can be adjusted after rule QA.
    length_m: float = 1.50
    width_m: float = 1.20
    robot_radius_m: float = 0.0375
    ball_radius_m: float = 0.0215
    home_goal_x_m: float = 0.0
    away_goal_x_m: float = 1.50


@dataclass
class VisionConfig:
    # Defaults for an orange ball. Tune from the HSV panel when lighting changes.
    ball_lower_hsv: Tuple[int, int, int] = (5, 80, 80)
    ball_upper_hsv: Tuple[int, int, int] = (25, 255, 255)
    ball_min_area_px: int = 80
    aruco_dictionary: str = "DICT_ARUCO_ORIGINAL"


@dataclass
class ControlConfig:
    wheel_base_m: float = 0.074
    max_wheel_mm_s: int = 1500
    max_linear_m_s: float = 0.65
    max_angular_rad_s: float = 7.0
    min_wheel_command_mm_s: int = 80
    position_tolerance_m: float = 0.045
    angle_kp: float = 3.5
    linear_kp: float = 1.4
    heading_slowdown_rad: float = 1.2
    velocity_multiplier: float = 0.10


@dataclass
class SerialConfig:
    port: str = ""
    baudrate: int = 115200
    send_hz: float = 20.0
    enabled: bool = False


@dataclass
class TeamConfig:
    # Marker id -> logical robot slot in the base-station packet, 1..5.
    marker_to_robot: Dict[int, int] = dataclass_field(
        default_factory=dict
    )


@dataclass
class AppConfig:
    field: FieldConfig = dataclass_field(default_factory=FieldConfig)
    vision: VisionConfig = dataclass_field(default_factory=VisionConfig)
    control: ControlConfig = dataclass_field(default_factory=ControlConfig)
    serial: SerialConfig = dataclass_field(default_factory=SerialConfig)
    team: TeamConfig = dataclass_field(default_factory=TeamConfig)
