import time
import math


class WorldModel:

    def __init__(self):
        self.ball_position = None
        self.ball_velocity = (0.0, 0.0)
        self.last_time = None
        self.last_position = None

    def update_ball(self, x, y):

        current_time = time.time()

        if self.last_position is not None:
            dt = current_time - self.last_time

            if dt > 0:
                vx = (x - self.last_position[0]) / dt
                vy = (y - self.last_position[1]) / dt
                self.ball_velocity = (vx, vy)

        self.ball_position = (x, y)
        self.last_position = (x, y)
        self.last_time = current_time

    def get_ball_speed(self):
        vx, vy = self.ball_velocity
        return math.sqrt(vx**2 + vy**2)
