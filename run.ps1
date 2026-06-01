$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

if (!(Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "No existe .venv, instalando dependencias primero..."
    & "$ProjectDir\install.ps1"
}

$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"

if ($args.Count -eq 0) {
    & $VenvPython main.py --camera mock
} else {
    & $VenvPython main.py @args
}
