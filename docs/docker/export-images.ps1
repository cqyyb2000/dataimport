# 在有网的 Windows（Docker Desktop）上构建并导出 Linux 镜像，供无网 Ubuntu 使用
# 用法：在 docs/docker 目录执行  .\export-images.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$OutDir = Join-Path $ScriptDir "offline-bundle\02-images"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$env:DOCKER_DEFAULT_PLATFORM = "linux/amd64"

Write-Host "==> pull mysql:8.0"
docker pull mysql:8.0

Write-Host "==> build backend + nginx"
docker compose build

Write-Host "==> save images to $OutDir"
docker save -o (Join-Path $OutDir "mysql-8.0.tar") mysql:8.0
docker save -o (Join-Path $OutDir "dataimport-backend.tar") dataimport-backend:latest
docker save -o (Join-Path $OutDir "dataimport-nginx.tar") dataimport-nginx:latest

Get-ChildItem $OutDir | Format-Table Name, @{N="SizeMB"; E={[math]::Round($_.Length/1MB,1)}}
Write-Host "Done. Copy offline-bundle to Ubuntu, then: docker load -i <file>.tar"
Write-Host "Start with: docker compose -f docker-compose.offline.yml up -d"
