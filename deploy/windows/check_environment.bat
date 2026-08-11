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
set "CHECK_FAILED=0"
set "DATABASE_READY=0"
set "SKIP_AUDIT=0"
set "ALLOW_RUNNING=0"
if /I "%~1"=="--skip-audit" set "SKIP_AUDIT=1"
if /I "%~1"=="--allow-running" set "ALLOW_RUNNING=1"

echo ==================================================
echo 生产环境检查（不会输出环境变量内容或服务器路径）
echo ==================================================

if not exist "%PYTHON_EXE%" (
  echo [FAIL] 后端虚拟环境不存在。
  exit /b 1
)

if not exist "%PRODUCTION_ENV%" (
  echo [FAIL] backend\.env.production 不存在。
  exit /b 1
)

for /f "delims=" %%V in ('"%PYTHON_EXE%" --version 2^>^&1') do echo [INFO] %%V

if exist "%ALEMBIC_EXE%" (
  for /f "delims=" %%V in ('"%ALEMBIC_EXE%" --version 2^>^&1') do echo [INFO] %%V
) else (
  echo [FAIL] Alembic 未安装。
  set "CHECK_FAILED=1"
)

pushd "%BACKEND_DIR%" || exit /b 1

"%PYTHON_EXE%" -c "from itertools import combinations; from pathlib import Path; from sqlalchemy.engine import make_url; from app.core.config import settings; root=Path(r'D:\script_material_data').resolve(); expected_db=(root/'database'/'script_materials.db').resolve(); expected_storage=(root/'storage').resolve(); expected_materials=(expected_storage/'materials').resolve(); expected_logs=(root/'logs').resolve(); expected_backups=(root/'backups').resolve(); expected_temp=(root/'temp').resolve(); expected_frontend=Path(r'D:\文档存储\frontend\dist').resolve(); url=make_url(settings.database_url); actual_db=Path(url.database or '').resolve(); top=[actual_db.parent,Path(settings.storage_root).resolve(),Path(settings.log_dir).resolve(),Path(settings.backup_root).resolve(),Path(settings.temp_root).resolve()]; materials=Path(settings.material_storage_path).resolve(); valid=settings.app_env=='production' and url.drivername=='sqlite' and actual_db==expected_db and top==[expected_db.parent,expected_storage,expected_logs,expected_backups,expected_temp] and materials==expected_materials and len(set(top))==len(top) and all(a!=b and a not in b.parents and b not in a.parents for a,b in combinations(top,2)) and all(materials!=p and materials not in p.parents and p not in materials.parents for p in [expected_db.parent,expected_logs,expected_backups,expected_temp]) and settings.serve_frontend is True and Path(settings.frontend_dist).resolve()==expected_frontend and str(settings.app_host)=='0.0.0.0' and settings.app_port==8000 and settings.api_prefix=='/api' and settings.debug is False; raise SystemExit(0 if valid else 1)" >nul 2>nul
if errorlevel 1 (
  echo [FAIL] 正式配置的数据路径隔离或固定运行参数无效；必须使用标准 D:\script_material_data、0.0.0.0:8000、/api 与指定 frontend\dist。
  popd
  exit /b 1
)
echo [OK] 正式数据路径配置与隔离规则通过。

"%PYTHON_EXE%" -c "from pathlib import Path; from sqlalchemy.engine import make_url; from app.core.config import settings; u=make_url(settings.database_url); p=Path(u.database or ''); raise SystemExit(0 if u.get_backend_name()!='sqlite' or p.is_file() else 1)" >nul 2>nul
if errorlevel 1 (
  echo [FAIL] 正式数据库不存在。
  set "CHECK_FAILED=1"
) else (
  echo [OK] 正式数据库存在。
  set "DATABASE_READY=1"
)

"%PYTHON_EXE%" -c "from pathlib import Path; import tempfile; from sqlalchemy.engine import make_url; from app.core.config import settings; u=make_url(settings.database_url); p=Path(u.database or ''); d=p.parent; f=tempfile.NamedTemporaryFile(dir=d,delete=False); n=Path(f.name); f.close(); n.unlink()" >nul 2>nul
if errorlevel 1 (
  echo [FAIL] 正式数据库目录不存在或不可写。
  set "CHECK_FAILED=1"
) else (
  echo [OK] 正式数据库目录可写。
)

"%PYTHON_EXE%" -c "from pathlib import Path; import tempfile; from app.core.config import settings; p=Path(settings.storage_root); p.mkdir(parents=True,exist_ok=True); f=tempfile.NamedTemporaryFile(dir=p,delete=False); n=Path(f.name); f.close(); n.unlink()" >nul 2>nul
if errorlevel 1 (
  echo [FAIL] storage 目录不存在或不可写。
  set "CHECK_FAILED=1"
) else (
  echo [OK] storage 目录可写。
)

"%PYTHON_EXE%" -c "from pathlib import Path; from app.core.config import settings; raise SystemExit(0 if Path(settings.frontend_dist,'index.html').is_file() else 1)" >nul 2>nul
if errorlevel 1 (
  echo [FAIL] 生产前端 dist 不存在或不完整。
  set "CHECK_FAILED=1"
) else (
  echo [OK] 生产前端 dist 存在。
)

set "APP_PORT_VALUE=8000"
set "PORT_OUTPUT=%TEMP%\script_material_port_%RANDOM%_%RANDOM%.txt"
"%PYTHON_EXE%" -c "from app.core.config import settings; print(settings.app_port)" > "%PORT_OUTPUT%" 2>nul
if errorlevel 1 (
  echo [FAIL] 无法读取生产端口配置。
  set "CHECK_FAILED=1"
) else (
  set /p APP_PORT_VALUE=<"%PORT_OUTPUT%"
)
del /q "%PORT_OUTPUT%" >nul 2>&1
netstat -ano -p TCP | findstr /R /C:":%APP_PORT_VALUE% .*LISTENING" >nul
if errorlevel 1 (
  echo [OK] 生产端口 %APP_PORT_VALUE% 未被占用。
) else (
  if "%ALLOW_RUNNING%"=="1" (
    echo [INFO] 生产端口 %APP_PORT_VALUE% 正在监听；运行中审计模式允许该状态。
  ) else (
    echo [FAIL] 生产端口 %APP_PORT_VALUE% 已被占用。
    set "CHECK_FAILED=1"
  )
)

if "%DATABASE_READY%"=="1" (
  if exist "%ALEMBIC_EXE%" (
    echo [INFO] 当前 Alembic 版本：
    "%ALEMBIC_EXE%" current
    if errorlevel 1 set "CHECK_FAILED=1"
  )
) else (
  echo [INFO] 数据库不存在，跳过 Alembic current。
)

if "%SKIP_AUDIT%"=="1" (
  echo [INFO] 本次为迁移前检查，数据审计将在迁移后执行。
) else (
  if "%DATABASE_READY%"=="1" (
    echo [INFO] 只读数据审计摘要：
    "%PYTHON_EXE%" -m app.tools.audit_data --fail-on-missing
    if errorlevel 1 (
      echo [FAIL] 数据审计失败或发现数据库引用的附件缺失。
      set "CHECK_FAILED=1"
    )
  ) else (
    echo [INFO] 数据库不存在，跳过数据审计。
  )
)

popd

if "%CHECK_FAILED%"=="0" (
  echo [OK] 生产环境检查通过。
  exit /b 0
)

echo [FAIL] 生产环境检查未通过，请修复上述问题后重试。
exit /b 1
