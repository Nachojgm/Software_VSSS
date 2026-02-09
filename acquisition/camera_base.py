class CameraBase:
    def open(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError
