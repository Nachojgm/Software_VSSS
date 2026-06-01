import numpy as np
import cv2
from acquisition.camera_base import CameraBase

try:
    import PySpin
except ImportError:  # Allows the app to run in mock/webcam mode without Spinnaker.
    PySpin = None


class GigECamera(CameraBase):
    def __init__(self):
        if PySpin is None:
            raise RuntimeError(
                "PySpin no esta instalado. Instala FLIR Spinnaker o usa --camera webcam/mock."
            )
        if not hasattr(PySpin, "System"):
            raise RuntimeError(
                "El modulo PySpin encontrado no es el SDK de FLIR/Spinnaker. "
                "Desinstala pyspin/PySpin de pip e instala el wheel oficial del SDK Spinnaker."
            )
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        if self.cam_list.GetSize() == 0:
            self.cam_list.Clear()
            self.system.ReleaseInstance()
            raise RuntimeError("No se encontro ninguna camara GigE/FLIR.")
        self.cam = self.cam_list[0]

    def open(self):
        self.cam.Init()

        nodemap = self.cam.GetNodeMap()

        # Pixel format -> BayerRG8
        pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
        pixel_format.SetIntValue(
            pixel_format.GetEntryByName("BayerRG8").GetValue()
        )

        # Acquisition mode -> Continuous
        acq = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
        acq.SetIntValue(
            acq.GetEntryByName("Continuous").GetValue()
        )


        self.cam.BeginAcquisition()

    def read(self):
        try:
            image = self.cam.GetNextImage(1000)
        except PySpin.SpinnakerException:
            return None

        if image.IsIncomplete():
            image.Release()
            return None

        img = image.GetNDArray()
        image.Release()

        # --- CONVERSIÃ“N PARA FLIR ---
        # BayerRG8 -> BGR
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)

        elif len(img.shape) == 3 and img.shape[2] == 1:
            img = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)

        elif len(img.shape) == 3 and img.shape[2] == 3:
            pass  # ya estÃ¡ bien

        else:
            raise RuntimeError(f"Formato no soportado: {img.shape}")

        return img


    def release(self):
        self.cam.EndAcquisition()
        self.cam.DeInit()
        self.cam_list.Clear()
        self.system.ReleaseInstance()
