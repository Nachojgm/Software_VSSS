# Software VSSS

Aplicacion de vision, estrategias y comunicacion para robots VSSS.

## Contrato con firmware

El firmware del robot en modo `MODO_BASESTATION` recibe por ESP-NOW un paquete con:

- `magic = 0xA5`
- `version = 1`
- `seq`
- 5 comandos de rueda: `left_mm_s`, `right_mm_s` como `int16`

La estacion base incluida en `Firmware/base-station-VSSL` expone ese protocolo al PC por serial con una linea:

```text
L1,R1,L2,R2,L3,R3,L4,R4,L5,R5
```

El firmware corta motores si no recibe comandos por mas de 200 ms, por eso este software transmite a 20 Hz cuando el envio esta activo.

## Instalacion rapida en Windows

Requisitos:

- Windows 10/11
- Python 3.10 de 64 bits
- Spinnaker SDK para camara GigE/FLIR
- Visual Studio Build Tools con C++ para compilar el puente C++ si no usas PySpin

Desde PowerShell, dentro de la carpeta `Software`:

```powershell
.\install.ps1
```

Tambien puedes hacer doble click en:

```text
install.bat
```

Luego prueba la app sin hardware:

```powershell
.\run.ps1 --camera mock
```

Para instalar y abrir en una sola llamada:

```powershell
.\install.ps1 -Run -Camera mock
```

## Camara GigE hibrida

El modo `gige` intenta dos caminos, en este orden:

1. PySpin oficial de FLIR/Spinnaker, si esta instalado para Python 3.10.
2. Puente C++ `bridge\build\spinnaker_bridge.exe`, que usa directamente el SDK Spinnaker y entrega frames a Python.

Esto permite correr la interfaz, vision y estrategias en Python, pero capturar la camara desde C++ cuando PySpin sea problematico.

Usar camara GigE:

```powershell
.\run.ps1 --camera gige
```

Forzar el puente C++:

```powershell
.\run.ps1 --camera gige-bridge
```

Compilar solo el puente C++:

```powershell
.\bridge\build_bridge.ps1
```

Si el build no encuentra Spinnaker:

```powershell
.\bridge\build_bridge.ps1 -SpinnakerRoot "C:\Program Files\Teledyne\Spinnaker"
```

## Comandos recomendados

Verificar entorno:

```powershell
.\.venv\Scripts\python.exe check_env.py
```

Probar sin hardware:

```powershell
.\run.ps1 --camera mock
```

Probar con webcam USB:

```powershell
.\run.ps1 --camera webcam
```

Usar camara GigE/FLIR sin enviar comandos:

```powershell
.\run.ps1 --camera gige
```

Usar camara GigE/FLIR y enviar comandos a la base station:

```powershell
.\run.ps1 --camera gige --port COM5 --send
```

Antes de usar `--send`, confirma que la base station esta conectada al puerto correcto y que los robots estan elevados o en una zona segura. El boton `STOP` manda ceros a los cinco robots.

## PySpin opcional

`opencv-contrib-python`, `numpy` y `pyserial` se instalan con `install.ps1`. El instalador tambien busca e instala automaticamente el wheel oficial de PySpin si encuentra Spinnaker SDK instalado o si copias el `.whl` a `Software\drivers`, `Software\vendor` o `Descargas`.

Comprueba si PySpin oficial esta listo con:

```powershell
.\.venv\Scripts\python.exe -c "import PySpin; print(PySpin.System.GetInstance())"
```

Si `import PySpin` funciona pero aparece un error como `module 'PySpin' has no attribute 'System'`, tienes instalado un paquete equivocado llamado `pyspin`/`PySpin` desde pip. Ese no es el SDK de FLIR.

## Calibracion

Haz click sobre la vista de la camara en las cuatro esquinas de la cancha:

1. Superior izquierda
2. Superior derecha
3. Inferior derecha
4. Inferior izquierda

Con eso las posiciones pasan de pixeles a metros. Las dimensiones estan centralizadas en `config.py` para ajustarlas con las reglas finales del torneo.
