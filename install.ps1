$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

function Find-Python {
    $candidates = @(
        "py -3",
        "python",
        "python3"
    )

    foreach ($candidate in $candidates) {
        $parts = $candidate.Split(" ")
        $exe = $parts[0]
        $candidateArgs = @()
        if ($parts.Length -gt 1) {
            $candidateArgs = $parts[1..($parts.Length - 1)]
        }
        try {
            if ($candidateArgs.Count -gt 0) {
                & $exe @candidateArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            } else {
                & $exe -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            }
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
        }
    }

    throw "No se encontro Python 3.10 o superior. Instala Python desde https://www.python.org/downloads/ y marca 'Add python.exe to PATH'."
}

$PythonCommand = Find-Python

if (!(Test-Path ".venv")) {
    Write-Host "Creando entorno virtual en Software\.venv"
    Invoke-Expression "$PythonCommand -m venv .venv"
}

$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"

Write-Host "Actualizando pip"
& $VenvPython -m pip install --upgrade pip

Write-Host "Instalando dependencias"
& $VenvPython -m pip install -r requirements.txt

Write-Host ""
Write-Host "Listo. Prueba con:"
Write-Host "  .\run.ps1 --camera mock"
