@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM =============================================================================
REM 若 NSSM 报错：No module named waitress --port=5501 app:app
REM 说明「应用程序参数」被错误地当成一个模块名，请用本脚本改回 run_waitress.py。
REM 管理员运行；按需修改下面三行。
REM =============================================================================

set "NSSM=D:\dataimport\nssm.exe"
set "SERVICE_NAME=DataImportBackend"
set "BACKEND_ROOT=D:\dataimport\backend"

set "VENV_PYTHON=%BACKEND_ROOT%\venv\Scripts\python.exe"
set "APP_ENTRY=%BACKEND_ROOT%\run_waitress.py"

if not exist "%NSSM%" (
  echo [错误] 找不到 NSSM: %NSSM%
  exit /b 1
)
if not exist "%APP_ENTRY%" (
  echo [错误] 找不到: %APP_ENTRY%
  exit /b 1
)

sc query %SERVICE_NAME% >nul 2>&1
if errorlevel 1 (
  echo [错误] 服务不存在: %SERVICE_NAME%
  exit /b 1
)

echo 停止服务...
net stop %SERVICE_NAME% 2>nul

echo 修正 Application / AppDirectory / AppParameters ...
"%NSSM%" set %SERVICE_NAME% Application "%VENV_PYTHON%"
"%NSSM%" set %SERVICE_NAME% AppDirectory "%BACKEND_ROOT%"
"%NSSM%" set %SERVICE_NAME% AppParameters "%APP_ENTRY%"

echo.
echo [完成] 已改为: python.exe + "%APP_ENTRY%"
echo 启动: net start %SERVICE_NAME%
echo.
pause
endlocal
