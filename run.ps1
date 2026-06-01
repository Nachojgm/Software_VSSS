$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

if (!(Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "No existe .venv, instalando dependencias primero..."
    & "$ProjectDir\install.ps1"
}

$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"

$UsesGige = $false
for ($i = 0; $i -lt $args.Count; $i++) {
    if ($args[$i] -eq "--camera" -and ($i + 1) -lt $args.Count -and $args[$i + 1] -eq "gige") {
        $UsesGige = $true
    }
}

if ($UsesGige) {
    & $VenvPython check_env.py --require-gige
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($args.Count -eq 0) {
    & $VenvPython main.py --camera mock
} else {
    & $VenvPython main.py @args
}
