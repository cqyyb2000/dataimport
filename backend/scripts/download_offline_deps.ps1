# 有网 Windows：按 requirements.txt 重新下载完整离线 wheel 到 offline_packages
# 用法（在 backend 目录）:  .\scripts\download_offline_deps.ps1

$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $BackendRoot

$Py = Join-Path $BackendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
  $Py = "python"
}

$Dest = Join-Path $BackendRoot "offline_packages"
$Tmp = Join-Path $BackendRoot "offline_packages_new"
$Req = Join-Path $BackendRoot "requirements.txt"
$OfflineReq = Join-Path $Dest "requirements-offline.txt"
$Readme = Join-Path $Dest "README.md"

if (Test-Path $Tmp) { Remove-Item $Tmp -Recurse -Force }
New-Item -ItemType Directory -Path $Tmp | Out-Null

Write-Host "==> download from $Req"
& $Py -m pip install -U pip wheel | Out-Null
& $Py -m pip download -r $Req -d $Tmp
& $Py -m pip download pip setuptools wheel -d $Tmp

# 保留说明与 ASCII 清单
$keep = @()
if (Test-Path $Readme) { $keep += Get-Item $Readme }
if (Test-Path $OfflineReq) { $keep += Get-Item $OfflineReq }

Get-ChildItem $Dest -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -in ".whl", ".tar.gz", ".zip" -or $_.Name -eq "install_requirements.txt" } |
  Remove-Item -Force

Copy-Item (Join-Path $Tmp "*") $Dest -Force
Remove-Item $Tmp -Recurse -Force

# 写 ASCII requirements（无中文，避免 Windows pip GBK 问题）
$lines = Get-Content $Req | Where-Object {
  $t = $_.Trim()
  $t -and -not $t.StartsWith("#")
}
@(
  "# Locked deps for offline install (ASCII only; mirrors requirements.txt)"
) + $lines | Set-Content -Path $OfflineReq -Encoding ascii

"pip install --no-index --find-links=. -r requirements-offline.txt" |
  Set-Content -Path (Join-Path $Dest "install_requirements.txt") -Encoding ascii

Write-Host "Done. Wheels in $Dest"
Get-ChildItem $Dest -Filter *.whl | Measure-Object | ForEach-Object { "whl count: $($_.Count)" }
