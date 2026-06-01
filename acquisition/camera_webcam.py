import cv2

from acquisition.camera_base import CameraBase


class WebcamCamera(CameraBase):
    def __init__(self, index=0):
        self.index = index
        self.capture = None

    def open(self):
        self.capture = cv2.VideoCapture(self.index)
        if not self.capture.isOpened():
            raise RuntimeError(f"No se pudo abrir la webcam {self.index}")

    def read(self):
        if self.capture is None:
            return None
        ok, frame = self.capture.read()
        return frame if ok else None

    def release(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
