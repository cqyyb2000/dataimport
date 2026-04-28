@echo off
chcp 65001 >nul
setlocal EnableExtensions

REM =============================================================================
REM 使用 NSSM 将后端注册为 Windows 服务（Flask + Waitress）
REM 请先：1）安装 NSSM  2）创建 D:\dataimport\backend\venv 并 pip install -r requirements.txt
REM 管理员：右键「以管理员身份运行」本脚本
REM -----------------------------------------------------------------------------
REM 与旧项目（如 flaskwebapi）NSSM「应用程序」页面对照：
REM   Path              -> 本脚本用 venv 的 python.exe（勿再用 C:\Python312\...）
REM   Startup directory -> %BACKEND_ROOT%（对应以前的 D:\docwebapi）
REM   Arguments         -> 仅用 run_waitress.py（或写绝对路径），不要用整段引号包 -m waitress ...
REM   常见错误：参数写成 "\"-m waitress --port=5501 app:app\"" 时，Python 会把整串当成模块名，
REM   报错：No module named waitress --port=5501 app:app
REM   若必须用 waitress 命令行：NSSM「参数」填 -m waitress --port=5501 app:app（勿给整行加外层引号）；
REM   或 cmd 下 nssm install 时勿写成第三个参数一整段引号，应类似：
REM   nssm install 服务名 "...\python.exe" -m waitress --port=5501 app:app
REM =============================================================================

set "BACKEND_ROOT=D:\dataimport\backend"
set "VENV_PYTHON=%BACKEND_ROOT%\venv\Scripts\python.exe"
set "APP_ENTRY=%BACKEND_ROOT%\run_waitress.py"
set "SERVICE_NAME=DataImportBackend"

REM NSSM 可执行文件（请改成你服务器上 nssm.exe 的实际路径，64 位系统用 win64 目录）
set "NSSM=D:\dataimport\nssm.exe"

if not exist "%NSSM%" (
  echo [错误] 找不到 NSSM: %NSSM%
  echo 请从 https://nssm.cc/download 下载，解压后修改本脚本中的 NSSM 变量。
  exit /b 1
)

if not exist "%VENV_PYTHON%" (
  echo [错误] 虚拟环境不存在: %VENV_PYTHON%
  echo 请先在 %BACKEND_ROOT% 下执行: python -m venv venv
  exit /b 1
)

if not exist "%APP_ENTRY%" (
  echo [错误] 找不到: %APP_ENTRY%
  exit /b 1
)

if not exist "%BACKEND_ROOT%\logs" mkdir "%BACKEND_ROOT%\logs" 2>nul

echo.
echo 服务名: %SERVICE_NAME%
echo 程序:   %VENV_PYTHON%
echo 参数:   %APP_ENTRY%
echo 目录:   %BACKEND_ROOT%
echo.

REM 若服务已存在，先提示（不自动删除，避免误操作）
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
  echo [警告] 服务 %SERVICE_NAME% 已存在。请先运行 uninstall_nssm_service.bat 再安装，或手动 sc delete。
  exit /b 1
)

"%NSSM%" install %SERVICE_NAME% "%VENV_PYTHON%" "%APP_ENTRY%"
if errorlevel 1 (
  echo [错误] nssm install 失败
  exit /b 1
)

"%NSSM%" set %SERVICE_NAME% AppDirectory "%BACKEND_ROOT%"
"%NSSM%" set %SERVICE_NAME% DisplayName "财政一体化-后端 API"
"%NSSM%" set %SERVICE_NAME% Description "Waitress 托管 Flask，工作目录 %BACKEND_ROOT%"
"%NSSM%" set %SERVICE_NAME% Start SERVICE_AUTO_START

REM 服务日志（与 app 内 logs\app.log 可同时使用）
"%NSSM%" set %SERVICE_NAME% AppStdout "%BACKEND_ROOT%\logs\nssm_stdout.log"
"%NSSM%" set %SERVICE_NAME% AppStderr "%BACKEND_ROOT%\logs\nssm_stderr.log"

REM 可选：进程退出后重启
"%NSSM%" set %SERVICE_NAME% AppExit Default Restart
"%NSSM%" set %SERVICE_NAME% AppRestartDelay 5000

echo.
echo [完成] 已注册服务。启动命令:
echo   net start %SERVICE_NAME%
echo 停止:
echo   net stop %SERVICE_NAME%
echo.
pause
endlocal
