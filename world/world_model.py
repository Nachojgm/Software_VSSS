import math
import time

from world.entities import Ball, Robot, WorldState


class WorldModel:

    def __init__(self):
        self.ball_position = None
        self.ball_velocity = (0.0, 0.0)
        self.last_time = None
        self.last_position = None
        self.robots = []
        self.ball = None

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
        if ball is not None and self.ball is not None and self.last_time is not None:
            dt = current_time - self.last_time
            if dt > 0:
                self.ball_velocity = (
                    (ball.x_m - self.ball.x_m) / dt,
                    (ball.y_m - self.ball.y_m) / dt,
                )
        elif ball is None:
            self.ball_velocity = (0.0, 0.0)

        self.ball = ball
        self.robots = list(robots)
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
