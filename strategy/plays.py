from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from config import AppConfig, NUM_ROBOTS
from control.differential import DifferentialController
from world.entities import WorldState


WheelCommand = Tuple[int, int]


@dataclass
class Play:
    key: str
    name: str
    description: str


class Playbook:
    def __init__(self, config: AppConfig):
        self.config = config
        self.controller = DifferentialController(config.control)
        self.plays = [
            Play("stop", "Detener", "Todos los robots quedan en cero."),
            Play("follow_ball", "Seguir pelota", "Los robots detectados se ordenan alrededor de la pelota."),
            Play("go_midfield", "Ir al medio", "El equipo se ordena alrededor del centro."),
            Play("spread_field", "Abrir cancha", "Cada robot toma una posicion distinta."),
            Play("attack_mode", "Modo ataque", "Formacion ofensiva hacia el arco rival."),
            Play("defense_mode", "Modo defensa", "Formacion defensiva frente al arco propio."),
        ]

    def commands_for(self, play_key: str, state: WorldState) -> List[WheelCommand]:
        robots_by_id = {robot.robot_id: robot for robot in state.robots}
        targets = self.targets_for(play_key, state)
        commands = []
        for robot_id in range(1, NUM_ROBOTS + 1):
            robot = robots_by_id.get(robot_id)
            target = targets.get(robot_id)
            commands.append(self.controller.go_to_pose(robot, target))
        return commands

    def targets_for(self, play_key: str, state: WorldState) -> Dict[int, Tuple[float, float]]:
        length = self.config.field.length_m
        width = self.config.field.width_m

        if play_key == "stop":
            return {}

        if play_key == "follow_ball":
            if not state.ball:
                return {}
            ball_x = state.ball.x_m
            ball_y = state.ball.y_m
            offsets = {
                1: (0.00, 0.00),
                2: (-0.14, -0.12),
                3: (-0.14, 0.12),
                4: (-0.28, -0.18),
                5: (-0.28, 0.18),
            }
            return {
                robot_id: (
                    max(0.05, min(length - 0.05, ball_x + offset_x)),
                    max(0.05, min(width - 0.05, ball_y + offset_y)),
                )
                for robot_id, (offset_x, offset_y) in offsets.items()
            }

        if play_key == "go_midfield":
            cx, cy = length * 0.5, width * 0.5
            return {
                1: (cx, cy),
                2: (cx - 0.15, cy - 0.20),
                3: (cx - 0.15, cy + 0.20),
                4: (cx + 0.15, cy - 0.20),
                5: (cx + 0.15, cy + 0.20),
            }

        if play_key == "spread_field":
            return {
                1: (length * 0.50, width * 0.50),
                2: (length * 0.25, width * 0.25),
                3: (length * 0.25, width * 0.75),
                4: (length * 0.70, width * 0.30),
                5: (length * 0.70, width * 0.70),
            }

        if play_key == "attack_mode":
            ball_y = state.ball.y_m if state.ball else width * 0.5
            return {
                1: (length * 0.78, ball_y),
                2: (length * 0.62, width * 0.35),
                3: (length * 0.62, width * 0.65),
                4: (length * 0.40, width * 0.35),
                5: (length * 0.25, width * 0.50),
            }

        if play_key == "defense_mode":
            ball_y = state.ball.y_m if state.ball else width * 0.5
            return {
                1: (length * 0.20, ball_y),
                2: (length * 0.30, width * 0.32),
                3: (length * 0.30, width * 0.68),
                4: (length * 0.45, width * 0.42),
                5: (length * 0.45, width * 0.58),
            }

        return {}

    def list(self) -> Iterable[Play]:
        return tuple(self.plays)
