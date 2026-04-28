@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM 管理员：右键「以管理员身份运行」
REM 与 install_nssm_service.bat 中的 NSSM、SERVICE_NAME 保持一致

set "SERVICE_NAME=DataImportBackend"
set "NSSM=C:\nssm\win64\nssm.exe"

if not exist "%NSSM%" (
  echo [错误] 找不到 NSSM: %NSSM%
  exit /b 1
)

sc query %SERVICE_NAME% >nul 2>&1
if errorlevel 1 (
  echo 服务 %SERVICE_NAME% 不存在，无需卸载。
  pause
  exit /b 0
)

echo 正在停止服务 %SERVICE_NAME% ...
net stop %SERVICE_NAME% 2>nul

echo 正在移除 NSSM 服务...
"%NSSM%" remove %SERVICE_NAME% confirm
if errorlevel 1 (
  echo [错误] nssm remove 失败，可尝试: sc delete %SERVICE_NAME%
  pause
  exit /b 1
)

echo [完成] 已移除服务 %SERVICE_NAME%
pause
endlocal
