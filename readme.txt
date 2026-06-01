# Sistema de visión para detección de pelota y robots

Este proyecto contiene scripts en Python para trabajar con una cámara GigE y realizar tareas de visión computacional orientadas a robótica, incluyendo:

- Captura de imágenes desde cámara FLIR/GigE
- Calibración HSV
- Selección de ROI de la cancha
- Selección manual de esquinas
- Detección de pelota por color
- Detección de robots mediante marcadores ArUco

## Requisitos

### Librerías de Python
Instalar con:

```bash
pip install numpy opencv-contrib-python