import argparse
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

import cv2

from acquisition.camera_gige import GigECamera
from acquisition.camera_mock import MockCamera
from acquisition.camera_spinnaker_bridge import SpinnakerBridgeCamera
from acquisition.camera_webcam import WebcamCamera
from comunication.base_station_serial import BaseStationSerial, CommandStreamer
from config import AppConfig, NUM_ROBOTS
from perception.pipeline import PerceptionPipeline
from strategy.plays import Playbook
from ui_overlay import draw_overlay
from world.world_model import WorldModel


class VSSSApp:
    def __init__(self, root, args):
        self.root = root
        self.args = args
        self.config = AppConfig()
        self.config.serial.port = args.port
        self.config.serial.enabled = args.send

        self.camera = self._create_camera(args.camera)
        self.pipeline = PerceptionPipeline(self.config)
        self.world = WorldModel()
        self.playbook = Playbook(self.config)
        self.selected_play = tk.StringVar(value="stop")
        self.send_enabled = tk.BooleanVar(value=args.send)
        self.velocity_multiplier = tk.DoubleVar(value=self.config.control.velocity_multiplier)
        self.velocity_multiplier_label = tk.StringVar()
        self.status_text = tk.StringVar(value="Inicializando")
        self.last_commands = [(0, 0)] * NUM_ROBOTS
        self.raw_commands = [(0, 0)] * NUM_ROBOTS
        self.corner_points = []
        self.display_origin = (0, 0)
        self.display_scale = 1.0
        self.photo = None
        self.running = True

        self.transport = BaseStationSerial(args.port, args.baud, self.config.control.max_wheel_mm_s)
        if args.send:
            self.transport.open()
        self.streamer = CommandStreamer(self.transport, hz=self.config.serial.send_hz)
        self.streamer.enabled = args.send
        self.streamer.start()

        self._build_ui()
        self.camera.open()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(10, self.loop)

    def _create_camera(self, camera_name):
        if camera_name == "gige":
            try:
                return GigECamera()
            except RuntimeError as exc:
                print(f"PySpin no disponible, usando puente C++ Spinnaker: {exc}")
                return SpinnakerBridgeCamera()
        if camera_name == "gige-bridge":
            return SpinnakerBridgeCamera()
        if camera_name == "webcam":
            return WebcamCamera(0)
        return MockCamera()

    def _build_ui(self):
        self.root.title("VSSS LARC - Vision y control")
        self.root.geometry("1240x820")

        container = ttk.Frame(self.root, padding=8)
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, width=900, height=675, background="#111111", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.add_corner)

        panel = ttk.Frame(container, width=300)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        ttk.Label(panel, text="Jugada").pack(anchor=tk.W)
        for play in self.playbook.list():
            ttk.Radiobutton(panel, text=play.name, value=play.key, variable=self.selected_play).pack(anchor=tk.W)

        ttk.Separator(panel).pack(fill=tk.X, pady=10)
        ttk.Label(panel, text="Multiplicador velocidad").pack(anchor=tk.W)
        ttk.Scale(
            panel,
            from_=0.01,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.velocity_multiplier,
            command=self.update_velocity_multiplier,
        ).pack(fill=tk.X)
        self._refresh_speed_label()
        self.velocity_multiplier.trace_add("write", self._refresh_speed_label)
        ttk.Label(panel, textvariable=self.velocity_multiplier_label).pack(anchor=tk.W)

        ttk.Separator(panel).pack(fill=tk.X, pady=10)
        ttk.Checkbutton(panel, text="Enviar a base station", variable=self.send_enabled, command=self.toggle_send).pack(anchor=tk.W)
        ttk.Button(panel, text="STOP", command=self.stop_now).pack(fill=tk.X, pady=6)
        ttk.Button(panel, text="Limpiar calibracion", command=self.clear_corners).pack(fill=tk.X)

        ttk.Separator(panel).pack(fill=tk.X, pady=10)
        self.info = tk.Text(panel, height=23, width=38)
        self.info.pack(fill=tk.BOTH, expand=True)
        ttk.Label(panel, textvariable=self.status_text).pack(anchor=tk.W, pady=(8, 0))

    def add_corner(self, event):
        if len(self.corner_points) >= 4:
            self.corner_points = []
        origin_x, origin_y = self.display_origin
        frame_x = (event.x - origin_x) / self.display_scale
        frame_y = (event.y - origin_y) / self.display_scale
        if frame_x < 0 or frame_y < 0:
            return
        self.corner_points.append((frame_x, frame_y))
        if len(self.corner_points) == 4:
            self.pipeline.set_field_corners(self.corner_points)

    def clear_corners(self):
        self.corner_points = []
        self.pipeline.homography = None

    def toggle_send(self):
        enabled = bool(self.send_enabled.get())
        if enabled and not self.transport.status.connected:
            self.transport.open()
        self.streamer.enabled = enabled

    def update_velocity_multiplier(self, _value=None):
        self.config.control.velocity_multiplier = float(self.velocity_multiplier.get())

    def stop_now(self):
        self.selected_play.set("stop")
        self.last_commands = [(0, 0)] * NUM_ROBOTS
        self.streamer.set_commands(self.last_commands)
        self.transport.stop_all()

    def loop(self):
        if not self.running:
            return

        frame = self.camera.read()
        if frame is not None:
            ball, robots = self.pipeline.process(frame)
            self.world.update(ball, robots)
            state = self.world.state()
            self.raw_commands = self.playbook.commands_for(self.selected_play.get(), state)
            self.last_commands = self._scale_commands(self.raw_commands)
            self.streamer.set_commands(self.last_commands)
            overlay = draw_overlay(frame, state, homography_ready=self.pipeline.homography is not None)
            self._draw_corner_points(overlay)
            self._show_frame(overlay)
            self._update_info(state)
        else:
            self.status_text.set("Sin frame de camara")

        self.root.after(30, self.loop)

    def _draw_corner_points(self, frame):
        if frame is None:
            return
        for index, point in enumerate(self.corner_points, start=1):
            cv2.circle(frame, (int(point[0]), int(point[1])), 7, (255, 255, 0), -1)
            cv2.putText(frame, str(index), (int(point[0]) + 8, int(point[1]) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    def _show_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = rgb.shape[:2]
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        scale = min(canvas_w / width, canvas_h / height)
        display_w = max(1, int(width * scale))
        display_h = max(1, int(height * scale))
        resized = cv2.resize(rgb, (display_w, display_h))
        ok, encoded = cv2.imencode(".ppm", resized)
        if not ok:
            return
        self.display_origin = ((canvas_w - display_w) // 2, (canvas_h - display_h) // 2)
        self.display_scale = scale
        self.photo = tk.PhotoImage(data=encoded.tobytes(), format="PPM")
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.photo, anchor=tk.CENTER)

    def _update_info(self, state):
        lines = []
        lines.append(f"Camara: {self.args.camera}")
        lines.append(f"Jugada: {self.selected_play.get()}")
        lines.append(f"Vel mult: {self.velocity_multiplier.get():.2f}")
        lines.append(f"Envio: {'ON' if self.streamer.enabled else 'OFF'}")
        lines.append(f"Serial: {self.transport.status.port or 'simulado'}")
        if self.transport.status.last_error:
            lines.append(f"Error serial: {self.transport.status.last_error}")
        lines.append("")
        if state.ball:
            lines.append(
                f"Pelota: x={state.ball.x_m:.3f} y={state.ball.y_m:.3f} "
                f"v=({state.ball.vx_m_s:.2f},{state.ball.vy_m_s:.2f})"
            )
        else:
            lines.append("Pelota: no detectada")
        lines.append("")
        for robot in state.robots:
            lines.append(
                f"R{robot.robot_id} M{robot.marker_id}: "
                f"x={robot.x_m:.3f} y={robot.y_m:.3f} "
                f"v=({robot.vx_m_s:.2f},{robot.vy_m_s:.2f}) th={robot.theta:.2f}"
            )
        lines.append("")
        lines.append("Comandos mm/s escalados:")
        for index, (left, right) in enumerate(self.last_commands, start=1):
            lines.append(f"R{index}: L={left:5d} R={right:5d}")
        lines.append("")
        lines.append("Calibracion: click 4 esquinas en orden TL, TR, BR, BL")

        self.info.delete("1.0", tk.END)
        self.info.insert(tk.END, "\n".join(lines))
        self.status_text.set("OK")

    def _scale_commands(self, commands):
        multiplier = max(0.01, min(1.0, float(self.velocity_multiplier.get())))
        return [
            (int(round(left * multiplier)), int(round(right * multiplier)))
            for left, right in commands
        ]

    def _refresh_speed_label(self, *_args):
        self.velocity_multiplier_label.set(f"{self.velocity_multiplier.get():.2f}x")

    def close(self):
        self.running = False
        self.streamer.stop()
        self.camera.release()
        self.transport.close()
        self.root.destroy()


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Software VSSS: vision, jugadas y comunicacion")
    parser.add_argument("--camera", choices=["gige", "gige-bridge", "webcam", "mock"], default="mock")
    parser.add_argument("--port", default="", help="Puerto serial de la base station, por ejemplo COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--send", action="store_true", help="Enviar comandos reales por serial")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    root = tk.Tk()
    VSSSApp(root, args)
    root.mainloop()


if __name__ == "__main__":
    main()
