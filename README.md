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
- Python 3.10 o superior
- Para camara GigE/FLIR: SDK FLIR Spinnaker instalado, incluyendo el modulo Python `PySpin`

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

Tambien puedes ejecutar `run.bat` con doble click. Si no pasas argumentos abre el modo `mock`, que sirve para verificar que la instalacion funciona.

## Instalacion rapida en Linux/Ubuntu

Requisitos:

- Ubuntu o derivado con `apt`
- Python 3.10 o superior
- Para camara GigE/FLIR: Spinnaker SDK para Linux instalado

Desde una terminal, dentro de la carpeta del repositorio:

```bash
bash install.sh
```

El instalador crea `.venv`, instala dependencias Python, instala paquetes de sistema necesarios (`python3-tk`, compilador C++ y similares) y trata de compilar el puente C++ de Spinnaker si el SDK esta disponible.

Prueba sin hardware:

```bash
bash run.sh --camera mock
```

Usar camara GigE/FLIR:

```bash
bash run.sh --camera gige
```

Enviar comandos a la base station en Linux:

```bash
bash run.sh --camera gige --port /dev/ttyUSB0 --send
```

El puerto puede ser `/dev/ttyUSB0`, `/dev/ttyACM0` u otro similar. Puedes listar puertos con:

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Si Linux no te deja abrir el puerto serial, agrega tu usuario al grupo `dialout` y vuelve a iniciar sesion:

```bash
sudo usermod -aG dialout $USER
```

Si ya tienes las dependencias de sistema instaladas o no quieres usar `sudo`:

```bash
bash install.sh --skip-apt
```

## Uso manual

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Probar sin hardware:

```bash
python main.py --camera mock
```

Usar webcam:

```bash
python main.py --camera webcam
```

Usar camara GigE/FLIR:

```bash
python main.py --camera gige
```

Enviar a la base station:

```bash
python main.py --camera gige --port COM5 --send
python main.py --camera gige --port /dev/ttyUSB0 --send
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

## Velocidad segura

La interfaz incluye un multiplicador de velocidad entre `0.01x` y `1.00x`. Parte en `0.10x` para pruebas seguras, y se aplica a las velocidades de rueda justo antes de enviarlas a la base station.

Recomendacion de prueba:

1. Ejecuta sin `--send` y verifica detecciones/comandos.
2. Usa `--send` con multiplicador bajo.
3. Sube progresivamente el multiplicador desde la interfaz.

## Tracking

El estado de pelota y robots se suaviza con un filtro Kalman 2D de velocidad constante. Esto reduce ruido de deteccion y entrega velocidades estimadas para estrategia/control.

## Camara GigE/FLIR y PySpin

`opencv-contrib-python`, `numpy` y `pyserial` se instalan con `install.ps1`. El instalador tambien busca e instala automaticamente el wheel oficial de PySpin si encuentra Spinnaker SDK instalado o si copias el `.whl` a `Software\drivers`, `Software\vendor` o `Descargas`.

Para usar `--camera gige`, el software intenta dos caminos:

1. PySpin oficial dentro del entorno Python.
2. Puente C++ `bridge\build\spinnaker_bridge.exe`, usando directamente el SDK Spinnaker.

El segundo camino evita depender del wheel de PySpin. Necesita Spinnaker SDK y Visual Studio Build Tools con C++.

Comprueba si esta listo con:

```powershell
.\.venv\Scripts\python.exe -c "import PySpin; print(PySpin.System.GetInstance())"
```

Si `import PySpin` funciona pero aparece un error como `module 'PySpin' has no attribute 'System'`, tienes instalado un paquete equivocado llamado `pyspin`/`PySpin` desde pip. Ese no es el SDK de FLIR. Corrige con:

```powershell
pip uninstall -y pyspin PySpin
```

Luego instala el `.whl` oficial que viene con Spinnaker para tu version de Python.

Si falla, la app igual puede correr en modo simulacion o webcam:

```powershell
.\run.ps1 --camera mock
.\run.ps1 --camera webcam
```

## Puente C++ Spinnaker

Para compilar solo el puente:

```powershell
.\bridge\build_bridge.ps1
```

En Linux/Ubuntu:

```bash
bash bridge/build_bridge.sh
```

Si el SDK esta instalado en una ruta no estandar:

```bash
SPINNAKER_ROOT=/opt/spinnaker bash bridge/build_bridge.sh
```

Para forzar su uso:

```powershell
.\run.ps1 --camera gige-bridge
```

En Linux/Ubuntu:

```bash
bash run.sh --camera gige-bridge
```

El modo normal tambien lo usa automaticamente si PySpin no esta disponible:

```powershell
.\run.ps1 --camera gige
```

## Calibracion

Haz click sobre la vista de la camara en las cuatro esquinas de la cancha:

1. Superior izquierda
2. Superior derecha
3. Inferior derecha
4. Inferior izquierda

Con eso las posiciones pasan de pixeles a metros. Las dimensiones estan centralizadas en `config.py` para ajustarlas con las reglas finales del torneo.
