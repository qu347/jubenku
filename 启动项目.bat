@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "BUNDLED_PYTHON=%PROJECT_ROOT%python_runtime\python.exe"
if exist "%BUNDLED_PYTHON%" (
  set "PYTHON_EXE=%BUNDLED_PYTHON%"
) else (
  set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
)
set "DATA_ROOT=%PROJECT_ROOT%.runtime\portable"
set "DB_DIR=%DATA_ROOT%\database"
set "DB_FILE=%DB_DIR%\script_materials.db"
set "STORAGE_DIR=%DATA_ROOT%\storage"
set "PACKAGE_DATA=%PROJECT_ROOT%portable_data"

title 剧本创作素材库 V1.0
echo.
echo ============================================================
echo   剧本创作素材库 V1.0 - 一键启动
echo ============================================================
echo.

if not exist "%BACKEND_DIR%\requirements.txt" (
  echo [错误] 当前目录不是完整项目，缺少 backend\requirements.txt。
  pause
  exit /b 1
)

if not exist "%PROJECT_ROOT%frontend\dist\index.html" (
  echo [错误] 缺少 frontend\dist\index.html，请重新获取完整项目包。
  pause
  exit /b 1
)

if not exist "%PYTHON_EXE%" (
  echo [准备] 未找到包内 Python 运行环境，正在创建...
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3.10 -m venv "%VENV_DIR%" >nul 2>&1
    if errorlevel 1 py -3 -m venv "%VENV_DIR%"
  ) else (
    where python >nul 2>&1
    if errorlevel 1 (
      echo [错误] 未安装 Python 3.10 或更高版本。
      echo [提示] 安装 Python 后再次双击本文件。
      pause
      exit /b 1
    )
    python -m venv "%VENV_DIR%"
  )
  if errorlevel 1 (
    echo [错误] Python 虚拟环境创建失败。
    pause
    exit /b 1
  )
)

"%PYTHON_EXE%" -c "import fastapi, sqlalchemy, alembic, uvicorn" >nul 2>&1
if errorlevel 1 (
  echo [准备] 正在安装后端依赖，首次运行可能需要几分钟...
  "%PYTHON_EXE%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
  if errorlevel 1 (
    echo [错误] 后端依赖安装失败，请检查网络后重试。
    pause
    exit /b 1
  )
)

if not exist "%DB_DIR%" mkdir "%DB_DIR%"
if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"
if not exist "%DATA_ROOT%\logs" mkdir "%DATA_ROOT%\logs"
if not exist "%DATA_ROOT%\backups" mkdir "%DATA_ROOT%\backups"
if not exist "%DATA_ROOT%\temp" mkdir "%DATA_ROOT%\temp"

set "FRESH_DATABASE=0"
if not exist "%DB_FILE%" (
  set "FRESH_DATABASE=1"
  if exist "%PACKAGE_DATA%\database\script_materials.db" (
    echo [准备] 正在恢复项目包内的数据快照...
    copy /y "%PACKAGE_DATA%\database\script_materials.db" "%DB_FILE%" >nul
    if errorlevel 1 (
      echo [错误] 数据库快照复制失败。
      pause
      exit /b 1
    )
  )
)

if exist "%PACKAGE_DATA%\storage\materials" if not exist "%STORAGE_DIR%\materials" (
  echo [准备] 正在恢复项目包内的素材附件...
  xcopy "%PACKAGE_DATA%\storage\materials" "%STORAGE_DIR%\materials\" /E /I /Q /Y >nul
  if errorlevel 2 (
    echo [错误] 素材附件复制失败。
    pause
    exit /b 1
  )
)

for %%V in (SETTINGS_ENV_FILE APP_ENV APP_HOST APP_PORT API_PREFIX DEBUG DATABASE_URL STORAGE_ROOT MATERIAL_STORAGE_PATH LOG_DIR BACKUP_ROOT TEMP_ROOT SERVE_FRONTEND FRONTEND_DIST CORS_ALLOWED_ORIGINS CORS_ORIGINS PYTHONOPTIMIZE) do set "%%V="
set "APP_ENV=production"
set "APP_HOST=127.0.0.1"
set "APP_PORT="
for /f "usebackq delims=" %%P in (`"%PYTHON_EXE%" "%BACKEND_DIR%\app\tools\select_port.py"`) do set "APP_PORT=%%P"
if not defined APP_PORT (
  echo [错误] 8000 至 8020 端口均不可用，请关闭占用程序后重试。
  pause
  exit /b 1
)
set "API_PREFIX=/api"
set "DEBUG=false"
set "DATABASE_URL=sqlite:///../.runtime/portable/database/script_materials.db"
set "STORAGE_ROOT=../.runtime/portable/storage"
set "MATERIAL_STORAGE_PATH=../.runtime/portable/storage/materials"
set "LOG_DIR=../.runtime/portable/logs"
set "BACKUP_ROOT=../.runtime/portable/backups"
set "TEMP_ROOT=../.runtime/portable/temp"
set "SERVE_FRONTEND=true"
set "FRONTEND_DIST=../frontend/dist"
set "CORS_ALLOWED_ORIGINS=http://127.0.0.1:%APP_PORT%,http://localhost:%APP_PORT%"
set "SETTINGS_ENV_FILE=%DATA_ROOT%\launcher.env"

pushd "%BACKEND_DIR%" || exit /b 1

echo [准备] 正在检查数据库版本...
"%PYTHON_EXE%" -m alembic upgrade head
if errorlevel 1 (
  echo [错误] 数据库迁移失败。
  popd
  pause
  exit /b 1
)

if "%FRESH_DATABASE%"=="1" if not exist "%PACKAGE_DATA%\database\script_materials.db" (
  echo [准备] 正在创建初始题材数据...
  "%PYTHON_EXE%" seed.py
  if errorlevel 1 (
    echo [错误] 初始化数据失败。
    popd
    pause
    exit /b 1
  )
)

echo.
echo [成功] 系统将在浏览器中打开：http://127.0.0.1:%APP_PORT%/materials
echo [提示] 请保持本窗口运行；需要停止时按 Ctrl+C。
echo.

start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:%APP_PORT%/materials'" >nul 2>&1
"%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port %APP_PORT% --workers 1
set "EXIT_CODE=%ERRORLEVEL%"

popd
if not "%EXIT_CODE%"=="0" (
  echo.
  echo [错误] 服务异常退出，退出码：%EXIT_CODE%
  echo [提示] 日志目录：.runtime\portable\logs
  pause
)
exit /b %EXIT_CODE%
