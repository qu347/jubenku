@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "ALEMBIC_EXE=%BACKEND_DIR%\.venv\Scripts\alembic.exe"
set "PRODUCTION_ENV=%BACKEND_DIR%\.env.production"
for %%V in (APP_HOST APP_PORT API_PREFIX DEBUG DATABASE_URL STORAGE_ROOT MATERIAL_STORAGE_PATH LOG_DIR BACKUP_ROOT TEMP_ROOT MAX_UPLOAD_MB BACKUP_RETENTION_DAYS SQLITE_BUSY_TIMEOUT_MS SQLITE_WAL_ENABLED SERVE_FRONTEND FRONTEND_DIST CORS_ALLOWED_ORIGINS CORS_ORIGINS LOG_MAX_BYTES LOG_BACKUP_COUNT PYTHONOPTIMIZE) do set "%%V="
set "APP_ENV=production"
set "SETTINGS_ENV_FILE=%PRODUCTION_ENV%"

echo [INFO] 模块化剧本题材素材库生产启动检查

if not exist "%PYTHON_EXE%" (
  echo [ERROR] 未找到后端虚拟环境：backend\.venv
  echo [HINT] 请先安装 Python 依赖，详见 docs\DEPLOYMENT.md。
  exit /b 1
)

if not exist "%ALEMBIC_EXE%" (
  echo [ERROR] 虚拟环境中未找到 Alembic。
  exit /b 1
)

if not exist "%PRODUCTION_ENV%" (
  echo [ERROR] 未找到 backend\.env.production。
  echo [HINT] 请复制 .env.production.example 后按部署环境填写；不要提交正式配置。
  exit /b 1
)

if not exist "%PROJECT_ROOT%\frontend\dist\index.html" (
  echo [ERROR] 未找到 frontend\dist\index.html。
  echo [HINT] 请先在 frontend 目录执行 pnpm install --frozen-lockfile 和 pnpm run build。
  exit /b 1
)

call "%SCRIPT_DIR%check_environment.bat" --skip-audit
if errorlevel 1 (
  echo [ERROR] 环境检查未通过，生产服务未启动。
  exit /b 1
)

pushd "%BACKEND_DIR%" || exit /b 1

echo [INFO] 执行数据库迁移：alembic upgrade head
"%ALEMBIC_EXE%" upgrade head
if errorlevel 1 (
  echo [ERROR] 数据库迁移失败，生产服务未启动。
  popd
  exit /b 1
)

echo [INFO] 检查模型与迁移一致性：alembic check
"%ALEMBIC_EXE%" check
if errorlevel 1 (
  echo [ERROR] Alembic 检查失败，生产服务未启动。
  popd
  exit /b 1
)

echo [INFO] 执行迁移后只读数据审计
"%PYTHON_EXE%" -m app.tools.audit_data --fail-on-missing
if errorlevel 1 (
  echo [ERROR] 数据审计失败或发现数据库引用的附件缺失，生产服务未启动。
  popd
  exit /b 1
)

set "UVICORN_HOST=0.0.0.0"
set "UVICORN_PORT=8000"
set "SERVER_OUTPUT=%TEMP%\script_material_server_%RANDOM%_%RANDOM%.txt"
"%PYTHON_EXE%" -c "from app.core.config import settings; print(str(settings.app_host) + chr(124) + str(settings.app_port))" > "%SERVER_OUTPUT%" 2>nul
if errorlevel 1 (
  echo [ERROR] 无法读取 APP_HOST 或 APP_PORT，生产服务未启动。
  del /q "%SERVER_OUTPUT%" >nul 2>&1
  popd
  exit /b 1
)
set /p SERVER_CONFIG=<"%SERVER_OUTPUT%"
del /q "%SERVER_OUTPUT%" >nul 2>&1
for /f "tokens=1,2 delims=|" %%A in ("%SERVER_CONFIG%") do (
  set "UVICORN_HOST=%%A"
  set "UVICORN_PORT=%%B"
)

echo [INFO] 当前环境：production
echo [INFO] 启动地址：http://%UVICORN_HOST%:%UVICORN_PORT%
echo [INFO] SQLite 生产部署固定使用 1 个 worker；按 Ctrl+C 可停止服务。
echo [INFO] 应用日志由后端轮转日志配置写入 LOG_DIR。

"%PYTHON_EXE%" -m uvicorn app.main:app --host "%UVICORN_HOST%" --port "%UVICORN_PORT%" --workers 1
set "EXIT_CODE=%ERRORLEVEL%"

popd
if not "%EXIT_CODE%"=="0" echo [ERROR] Uvicorn 异常退出，退出码 %EXIT_CODE%。请查看 application.log 和 error.log。
exit /b %EXIT_CODE%
