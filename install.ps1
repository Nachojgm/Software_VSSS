param(
    [switch]$Run,
    [ValidateSet("mock", "webcam", "gige")]
    [string]$Camera = "mock",
    [string]$Port = "",
    [switch]$Send,
    [switch]$SkipSpinnaker
)

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

function Invoke-Checked {
    param(
        [string]$Description,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo: $Description"
    }
}

function Find-Python310 {
    $candidates = @(
        @("py", "-3.10"),
        @("python"),
        @("python3")
    )

    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        $candidateArgs = @()
        if ($candidate.Length -gt 1) {
            $candidateArgs = $candidate[1..($candidate.Length - 1)]
        }

        try {
            & $exe @candidateArgs -c "import platform, sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) and platform.architecture()[0] == '64bit' else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return @{
                    Exe = $exe
                    Args = $candidateArgs
                    CommandText = (($candidate -join " ").Trim())
                }
            }
        } catch {
        }
    }

    return $null
}

function Install-Python310 {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        throw "No se encontro Python 3.10 64-bit ni winget para instalarlo. Instala Python 3.10.x 64-bit desde https://www.python.org/downloads/release/python-31011/ y vuelve a correr .\install.ps1"
    }

    Invoke-Checked "Instalando Python 3.10 con winget" {
        winget install --id Python.Python.3.10 --source winget --scope user --accept-package-agreements --accept-source-agreements
    }
}

function Get-VenvStatus {
    $venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    if (!(Test-Path $venvPython)) {
        return "missing"
    }

    & $venvPython -c "import platform, sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) and platform.architecture()[0] == '64bit' else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        return "wrong-python"
    }

    return "ok"
}

function Reset-Venv {
    $venvPath = Join-Path $ProjectDir ".venv"
    if (!(Test-Path $venvPath)) {
        return
    }

    $resolvedProject = (Resolve-Path $ProjectDir).Path
    $resolvedVenv = (Resolve-Path $venvPath).Path
    if (!$resolvedVenv.StartsWith($resolvedProject)) {
        throw "Ruta .venv insegura: $resolvedVenv"
    }

    Write-Host "Eliminando .venv anterior para evitar mezclas de Python/NumPy"
    Remove-Item -LiteralPath $resolvedVenv -Recurse -Force
}

function Test-OfficialPySpin {
    param([string]$PythonExe)

    & $PythonExe -c "import importlib.util, sys; spec=importlib.util.find_spec('PySpin'); sys.exit(1 if spec is None else 0); import PySpin" 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    & $PythonExe -c "import PySpin, sys; sys.exit(0 if hasattr(PySpin, 'System') else 1)" 2>$null
    return $LASTEXITCODE -eq 0
}

function Find-SpinnakerWheel {
    $patterns = @(
        "spinnaker_python*cp310*win_amd64.whl",
        "spinnaker_python*py3*none*win_amd64.whl",
        "spinnaker_python*.whl"
    )

    $roots = @(
        $ProjectDir,
        (Join-Path $ProjectDir "drivers"),
        (Join-Path $ProjectDir "vendor"),
        "$env:USERPROFILE\Downloads",
        "$env:ProgramFiles",
        "${env:ProgramFiles(x86)}"
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($root in $roots) {
        foreach ($pattern in $patterns) {
            $match = Get-ChildItem -LiteralPath $root -Recurse -Filter $pattern -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            if ($null -ne $match) {
                return $match.FullName
            }
        }
    }

    return $null
}

Write-Host "Instalador VSSS"
Write-Host "Carpeta: $ProjectDir"

$Python310 = Find-Python310
if ($null -eq $Python310) {
    Install-Python310
    $Python310 = Find-Python310
}

if ($null -eq $Python310) {
    throw "No se pudo encontrar Python 3.10 64-bit despues de la instalacion."
}

Write-Host "Python seleccionado: $($Python310.CommandText)"

$venvStatus = Get-VenvStatus
if ($venvStatus -eq "wrong-python") {
    Reset-Venv
    $venvStatus = "missing"
}

if ($venvStatus -eq "missing") {
    Invoke-Checked "Creando entorno virtual con Python 3.10" {
        $pythonArgs = $Python310.Args
        & $Python310.Exe @pythonArgs -m venv .venv
    }
} else {
    Write-Host "Usando entorno virtual existente .venv"
}

$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"

Invoke-Checked "Actualizando pip/setuptools/wheel" {
    & $VenvPython -m pip install --upgrade pip setuptools wheel
}

Invoke-Checked "Instalando dependencias Python limpias" {
    & $VenvPython -m pip install --upgrade --force-reinstall -r requirements.txt
}

if (!$SkipSpinnaker) {
    if (Test-OfficialPySpin $VenvPython) {
        Write-Host "PySpin oficial de Spinnaker ya esta instalado."
    } else {
        Write-Host "PySpin oficial no esta disponible. Buscando wheel de Spinnaker para Python 3.10..."
        & $VenvPython -m pip uninstall -y pyspin PySpin spinnaker-python spinnaker_python 2>$null

        $wheel = Find-SpinnakerWheel
        if ($null -eq $wheel) {
            Write-Host ""
            Write-Host "No encontre el wheel oficial de Spinnaker/PySpin."
            Write-Host "Instala FLIR/Teledyne Spinnaker SDK para Windows o copia el wheel a una de estas rutas:"
            Write-Host "  - Software\drivers"
            Write-Host "  - Software\vendor"
            Write-Host "  - Descargas"
            Write-Host ""
            Write-Host "El archivo suele llamarse parecido a:"
            Write-Host "  spinnaker_python-*-cp310-cp310-win_amd64.whl"
            Write-Host ""
            Write-Host "Puedes usar la app en modo mock/webcam mientras tanto."
        } else {
            Invoke-Checked "Instalando PySpin desde $wheel" {
                & $VenvPython -m pip install --force-reinstall $wheel
            }
        }
    }
}

Invoke-Checked "Verificando entorno" {
    & $VenvPython check_env.py
}

Write-Host ""
Write-Host "Instalacion lista."
Write-Host "Prueba sin hardware:"
Write-Host "  .\run.ps1 --camera mock"
Write-Host "Prueba GigE:"
Write-Host "  .\run.ps1 --camera gige"

if ($Run) {
    $runArgs = @("--camera", $Camera)
    if ($Port) {
        $runArgs += @("--port", $Port)
    }
    if ($Send) {
        $runArgs += "--send"
    }
    & "$ProjectDir\run.ps1" @runArgs
}
