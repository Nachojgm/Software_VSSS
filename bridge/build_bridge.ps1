param(
    [string]$SpinnakerRoot = ""
)

$ErrorActionPreference = "Stop"
$BridgeDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildDir = Join-Path $BridgeDir "build"
$Source = Join-Path $BridgeDir "spinnaker_bridge.cpp"
$Output = Join-Path $BuildDir "spinnaker_bridge.exe"

function Find-SpinnakerRoot {
    if ($SpinnakerRoot -and (Test-Path $SpinnakerRoot)) {
        return (Resolve-Path $SpinnakerRoot).Path
    }

    $candidates = @(
        "$env:ProgramFiles\Teledyne\Spinnaker",
        "$env:ProgramFiles\FLIR Systems\Spinnaker",
        "$env:ProgramFiles\Point Grey Research\Spinnaker",
        "${env:ProgramFiles(x86)}\Teledyne\Spinnaker",
        "${env:ProgramFiles(x86)}\FLIR Systems\Spinnaker"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path (Join-Path $candidate "include\Spinnaker.h"))) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw "No se encontro Spinnaker SDK. Instala FLIR/Teledyne Spinnaker o usa -SpinnakerRoot."
}

function Import-VcVars {
    if (Get-Command cl.exe -ErrorAction SilentlyContinue) {
        return
    }

    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (!(Test-Path $vswhere)) {
        throw "No se encontro compilador C++ de Visual Studio. Instala 'Visual Studio Build Tools' con C++."
    }

    $installPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (!$installPath) {
        throw "No se encontro workload C++ de Visual Studio Build Tools."
    }

    $vcvars = Join-Path $installPath "VC\Auxiliary\Build\vcvars64.bat"
    if (!(Test-Path $vcvars)) {
        throw "No se encontro vcvars64.bat."
    }

    $envLines = cmd /c "`"$vcvars`" >nul && set"
    foreach ($line in $envLines) {
        $pair = $line -split "=", 2
        if ($pair.Length -eq 2) {
            Set-Item -Path "Env:\$($pair[0])" -Value $pair[1]
        }
    }
}

function Find-SpinnakerLib {
    param([string]$Root)

    $libDirs = @(
        (Join-Path $Root "lib64"),
        (Join-Path $Root "lib64\vs2015"),
        (Join-Path $Root "lib64\vs2017"),
        (Join-Path $Root "lib64\vs2019"),
        (Join-Path $Root "lib64\vs2022")
    ) | Where-Object { Test-Path $_ }

    foreach ($dir in $libDirs) {
        $libs = Get-ChildItem -LiteralPath $dir -Filter "Spinnaker*.lib" -ErrorAction SilentlyContinue
        $lib = $libs |
            Where-Object { $_.Name -match '^Spinnaker(_v[0-9]+)?\.lib$' } |
            Sort-Object Name |
            Select-Object -First 1
        if ($null -eq $lib) {
            $lib = $libs |
                Where-Object { $_.Name -notmatch '^SpinnakerC' -and $_.Name -notmatch 'd(_v[0-9]+)?\.lib$' } |
                Sort-Object Name |
                Select-Object -First 1
        }
        if ($null -ne $lib) {
            return $lib.FullName
        }
    }

    throw "No se encontro la libreria C++ Spinnaker dentro de $Root\lib64."
}

$root = Find-SpinnakerRoot
$includeDir = Join-Path $root "include"
$libPath = Find-SpinnakerLib $root

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
Import-VcVars

Write-Host "Compilando puente Spinnaker"
Write-Host "SDK: $root"
Write-Host "LIB: $libPath"

& cl.exe /nologo /std:c++17 /EHsc /O2 /I"$includeDir" "$Source" "$libPath" /Fe"$Output"
if ($LASTEXITCODE -ne 0) {
    throw "Fallo compilando spinnaker_bridge.exe"
}

Write-Host "Bridge listo: $Output"
