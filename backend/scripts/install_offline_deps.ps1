# 无网 Windows：用 offline_packages 安装到本地 venv
# 用法（在 backend 目录）:  .\scripts\install_offline_deps.ps1

$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $BackendRoot

$Off = Join-Path $BackendRoot "offline_packages"
$Req = Join-Path $Off "requirements-offline.txt"
$VenvPy = Join-Path $BackendRoot "venv\Scripts\python.exe"

if (-not (Test-Path $Req)) {
  throw "Missing $Req — run download_offline_deps.ps1 on a machine with internet first."
}

if (-not (Test-Path $VenvPy)) {
  Write-Host "==> create venv"
  python -m venv (Join-Path $BackendRoot "venv")
}

Write-Host "==> bootstrap pip"
& $VenvPy -m pip install --upgrade --no-index --find-links $Off pip setuptools wheel

Write-Host "==> install requirements-offline.txt"
& $VenvPy -m pip install --no-index --find-links $Off -r $Req

Write-Host "Done. Activate: .\venv\Scripts\activate"
