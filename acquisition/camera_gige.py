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
        self.last_status = ""
        self.last_error = ""

    def open(self):
        self.cam.Init()

        nodemap = self.cam.GetNodeMap()
        stream_nodemap = self.cam.GetTLStreamNodeMap()

        self._set_enum_if_available(stream_nodemap, "StreamBufferHandlingMode", "NewestOnly")
        self._set_enum_if_available(nodemap, "AcquisitionMode", "Continuous")

        # Pixel format -> BayerRG8
        self._set_enum_if_available(nodemap, "PixelFormat", "BayerRG8")

        self.cam.BeginAcquisition()
        self.last_status = "PySpin listo"

    def read(self):
        try:
            image = self.cam.GetNextImage(30)
        except PySpin.SpinnakerException as exc:
            self.last_error = str(exc)
            return None

        if image.IsIncomplete():
            self.last_error = "Frame incompleto"
            image.Release()
            return None

        img = image.GetNDArray()
        image.Release()

        # BayerRG8 -> BGR
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)

        elif len(img.shape) == 3 and img.shape[2] == 1:
            img = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)

        elif len(img.shape) == 3 and img.shape[2] == 3:
            pass

        else:
            raise RuntimeError(f"Formato no soportado: {img.shape}")

        return img


    def release(self):
        try:
            self.cam.EndAcquisition()
        except Exception:
            pass
        try:
            self.cam.DeInit()
        except Exception:
            pass
        self.cam_list.Clear()
        self.system.ReleaseInstance()

    def _set_enum_if_available(self, nodemap, node_name, entry_name):
        node = PySpin.CEnumerationPtr(nodemap.GetNode(node_name))
        if not PySpin.IsAvailable(node) or not PySpin.IsWritable(node):
            return False
        entry = node.GetEntryByName(entry_name)
        if not PySpin.IsAvailable(entry) or not PySpin.IsReadable(entry):
            return False
        node.SetIntValue(entry.GetValue())
        return True
