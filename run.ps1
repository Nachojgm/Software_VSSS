$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

if (!(Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "No existe .venv, instalando dependencias primero..."
    & "$ProjectDir\install.ps1"
}

$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"

$cameraArg = ""
for ($i = 0; $i -lt $args.Count; $i++) {
    if ($args[$i] -eq "--camera" -and ($i + 1) -lt $args.Count) {
        $cameraArg = $args[$i + 1]
    }
}

if ($cameraArg -eq "gige" -or $cameraArg -eq "gige-bridge") {
    $bridgeExe = Join-Path $ProjectDir "bridge\build\spinnaker_bridge.exe"
    $bridgeSource = Join-Path $ProjectDir "bridge\spinnaker_bridge.cpp"
    $bridgeBuild = Join-Path $ProjectDir "bridge\build_bridge.ps1"
    $needsBridge = !(Test-Path $bridgeExe)
    if (!$needsBridge -and (Test-Path $bridgeSource)) {
        $needsBridge = (Get-Item -LiteralPath $bridgeSource).LastWriteTimeUtc -gt (Get-Item -LiteralPath $bridgeExe).LastWriteTimeUtc
    }
    if (!$needsBridge -and (Test-Path $bridgeBuild)) {
        $needsBridge = (Get-Item -LiteralPath $bridgeBuild).LastWriteTimeUtc -gt (Get-Item -LiteralPath $bridgeExe).LastWriteTimeUtc
    }
    if ($needsBridge -and (Test-Path $bridgeBuild)) {
        Write-Host "Compilando/actualizando puente C++ Spinnaker..."
        try {
            & $bridgeBuild
        } catch {
            Write-Host "No se pudo compilar el puente C++ Spinnaker: $($_.Exception.Message)"
        }
    }
}

if ($args.Count -eq 0) {
    & $VenvPython main.py --camera mock
} else {
    & $VenvPython main.py @args
}
