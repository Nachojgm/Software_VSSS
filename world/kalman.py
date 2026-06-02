import math

import numpy as np


def wrap_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class ConstantVelocityKalman2D:
    """Linear Kalman filter for [x, y, vx, vy]."""

    def __init__(self, process_noise=0.4, measurement_noise=0.02):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.x = np.zeros((4, 1), dtype=float)
        self.p = np.eye(4, dtype=float)
        self.initialized = False

    def update(self, mx, my, dt):
        dt = max(1e-3, min(float(dt), 0.25))
        if not self.initialized:
            self.x[:, 0] = [mx, my, 0.0, 0.0]
            self.p = np.diag([0.02, 0.02, 1.0, 1.0])
            self.initialized = True
            return self.state()

        f = np.array(
            [
                [1.0, 0.0, dt, 0.0],
                [0.0, 1.0, 0.0, dt],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        h = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=float,
        )

        q_scale = self.process_noise
        q = q_scale * np.array(
            [
                [dt**4 / 4.0, 0.0, dt**3 / 2.0, 0.0],
                [0.0, dt**4 / 4.0, 0.0, dt**3 / 2.0],
                [dt**3 / 2.0, 0.0, dt**2, 0.0],
                [0.0, dt**3 / 2.0, 0.0, dt**2],
            ],
            dtype=float,
        )
        r = np.eye(2, dtype=float) * self.measurement_noise

        self.x = f @ self.x
        self.p = f @ self.p @ f.T + q

        z = np.array([[mx], [my]], dtype=float)
        innovation = z - h @ self.x
        s = h @ self.p @ h.T + r
        k = self.p @ h.T @ np.linalg.inv(s)
        self.x = self.x + k @ innovation
        self.p = (np.eye(4, dtype=float) - k @ h) @ self.p
        return self.state()

    def state(self):
        return tuple(float(v) for v in self.x[:, 0])


class AngleTracker:
    def __init__(self):
        self.theta = 0.0
        self.angular_velocity = 0.0
        self.initialized = False

    def update(self, theta, dt):
        dt = max(1e-3, min(float(dt), 0.25))
        if not self.initialized:
            self.theta = theta
            self.angular_velocity = 0.0
            self.initialized = True
            return self.theta, self.angular_velocity

        delta = wrap_angle(theta - self.theta)
        measured_omega = delta / dt
        self.theta = wrap_angle(self.theta + 0.55 * delta)
        self.angular_velocity = 0.7 * self.angular_velocity + 0.3 * measured_omega
        return self.theta, self.angular_velocity
