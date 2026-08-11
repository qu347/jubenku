@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "PRODUCTION_ENV=%BACKEND_DIR%\.env.production"
for %%V in (APP_HOST APP_PORT API_PREFIX DEBUG DATABASE_URL STORAGE_ROOT MATERIAL_STORAGE_PATH LOG_DIR BACKUP_ROOT TEMP_ROOT MAX_UPLOAD_MB BACKUP_RETENTION_DAYS SQLITE_BUSY_TIMEOUT_MS SQLITE_WAL_ENABLED SERVE_FRONTEND FRONTEND_DIST CORS_ALLOWED_ORIGINS CORS_ORIGINS LOG_MAX_BYTES LOG_BACKUP_COUNT PYTHONOPTIMIZE) do set "%%V="
set "APP_ENV=production"
set "SETTINGS_ENV_FILE=%PRODUCTION_ENV%"

if not exist "%PYTHON_EXE%" (
  echo [ERROR] 未找到 backend\.venv，无法执行备份。
  exit /b 1
)

if not exist "%PRODUCTION_ENV%" (
  echo [ERROR] 未找到 backend\.env.production，无法确定正式数据目录。
  exit /b 1
)

pushd "%BACKEND_DIR%" || exit /b 1
"%PYTHON_EXE%" -c "from itertools import combinations; from pathlib import Path; from sqlalchemy.engine import make_url; from app.core.config import settings; root=Path(r'D:\script_material_data').resolve(); expected_db=(root/'database'/'script_materials.db').resolve(); expected_storage=(root/'storage').resolve(); expected_materials=(expected_storage/'materials').resolve(); expected_logs=(root/'logs').resolve(); expected_backups=(root/'backups').resolve(); expected_temp=(root/'temp').resolve(); expected_frontend=Path(r'D:\文档存储\frontend\dist').resolve(); url=make_url(settings.database_url); actual_db=Path(url.database or '').resolve(); top=[actual_db.parent,Path(settings.storage_root).resolve(),Path(settings.log_dir).resolve(),Path(settings.backup_root).resolve(),Path(settings.temp_root).resolve()]; materials=Path(settings.material_storage_path).resolve(); valid=settings.app_env=='production' and url.drivername=='sqlite' and actual_db==expected_db and top==[expected_db.parent,expected_storage,expected_logs,expected_backups,expected_temp] and materials==expected_materials and len(set(top))==len(top) and all(a!=b and a not in b.parents and b not in a.parents for a,b in combinations(top,2)) and all(materials!=p and materials not in p.parents and p not in materials.parents for p in [expected_db.parent,expected_logs,expected_backups,expected_temp]) and settings.serve_frontend is True and Path(settings.frontend_dist).resolve()==expected_frontend and str(settings.app_host)=='0.0.0.0' and settings.app_port==8000 and settings.api_prefix=='/api' and settings.debug is False; raise SystemExit(0 if valid else 1)" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] 正式配置的数据路径隔离或固定运行参数无效，拒绝执行备份。
  popd
  exit /b 1
)
echo [OK] 正式数据路径配置与隔离规则通过。
echo [INFO] 开始一致性备份；不会删除正式数据库或 storage 文件。
"%PYTHON_EXE%" -m app.tools.backup
set "EXIT_CODE=%ERRORLEVEL%"
popd

if not "%EXIT_CODE%"=="0" (
  echo [ERROR] 备份或备份验证失败，退出码 %EXIT_CODE%。失败目录不会被标记为成功。
  exit /b %EXIT_CODE%
)

echo [OK] 备份及验证完成。请定期执行恢复到测试目录的演练。
exit /b 0
