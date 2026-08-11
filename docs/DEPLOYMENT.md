# Windows 企业内网生产部署说明

## 1. 部署原则

- 应用代码位于 `D:\文档存储`，正式数据位于 `D:\script_material_data`，两者必须分离。
- 正式数据库从原开发数据库复制后迁移；禁止用 Sprint 3 验收数据库覆盖正式数据。
- 生产前端由 FastAPI 托管，不运行 Vite 开发服务器或 5173 端口。
- SQLite 只使用一个 Uvicorn worker，禁止 `--reload`。
- 系统没有登录和权限功能，只允许企业内网指定网段访问，禁止公网暴露。

## 2. 环境要求

- Windows 10/11 或 Windows Server 2019 及以上。
- 64 位 Python 3.10 或更高兼容版本。
- Node.js 20 LTS 或更高兼容版本。
- pnpm 9 或更高兼容版本。
- 至少预留“当前数据库 + 当前附件 + 两份完整备份 + 20%”的磁盘空间。
- 部署账户对代码目录有读取/执行权限，对 `D:\script_material_data` 有修改权限。
- 管理 Windows 防火墙时需要管理员权限。

检查版本：

```powershell
python --version
node --version
pnpm --version
```

## 3. 安装后端依赖

```powershell
cd D:\文档存储\backend
& python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw '创建后端虚拟环境失败。' }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip 升级失败。' }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw '后端依赖安装失败。' }
```

不要把虚拟环境复制到其他 Python 版本的机器；应在目标服务器重新创建。

## 4. 构建生产前端

```powershell
cd D:\文档存储\frontend
& pnpm install --frozen-lockfile
if ($LASTEXITCODE -ne 0) { throw '前端依赖安装失败。' }
& pnpm run type-check
if ($LASTEXITCODE -ne 0) { throw 'TypeScript 检查失败。' }
& pnpm run test:unit
if ($LASTEXITCODE -ne 0) { throw '前端单元测试失败。' }
& pnpm run build
if ($LASTEXITCODE -ne 0) { throw '前端生产构建失败。' }
```

构建结果必须包含 `D:\文档存储\frontend\dist\index.html` 和 `dist\assets`。ECharts 或 Element Plus 超过 500KB 的构建提示不是发布阻塞项。生产环境只访问 8000 端口；不得启动 `pnpm run dev` 或把 `127.0.0.1:5173` 写入生产包。

## 5. 建立正式数据目录

在生产服务器执行：

```powershell
$dataRoot = 'D:\script_material_data'
@('database','storage\materials','backups','logs','temp') | ForEach-Object {
    New-Item -ItemType Directory -Path (Join-Path $dataRoot $_) -Force | Out-Null
}
```

最终结构：

```text
D:\script_material_data\
├─ database\script_materials.db
├─ storage\materials\YYYY\MM\
├─ backups\
├─ logs\
└─ temp\
```

应用更新只能替换 `D:\文档存储` 内的代码，不能覆盖或清空上述数据目录。

## 6. 配置生产环境

复制示例后编辑正式配置：

```powershell
$envExample = 'D:\文档存储\backend\.env.production.example'
$productionEnv = 'D:\文档存储\backend\.env.production'
if (Test-Path -LiteralPath $productionEnv) {
    throw '.env.production 已存在，禁止用示例配置覆盖；请由管理员人工复核现有配置。'
}
Copy-Item -LiteralPath $envExample -Destination $productionEnv -ErrorAction Stop
```

复制成功后使用管理员批准的文本编辑器修改 `$productionEnv`；不要在工单、聊天或截图中公开正式配置内容。

最低配置：

```dotenv
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=sqlite:///D:/script_material_data/database/script_materials.db
STORAGE_ROOT=D:/script_material_data/storage
LOG_DIR=D:/script_material_data/logs
BACKUP_ROOT=D:/script_material_data/backups
TEMP_ROOT=D:/script_material_data/temp
MAX_UPLOAD_MB=100
SERVE_FRONTEND=true
FRONTEND_DIST=D:/文档存储/frontend/dist
BACKUP_RETENTION_DAYS=30
CORS_ALLOWED_ORIGINS=
SQLITE_BUSY_TIMEOUT_MS=5000
SQLITE_WAL_ENABLED=true
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=10
```

Windows 路径建议在 URL 和环境文件中使用 `/`。`.env.production` 不得提交到 Git，不应包含密码或用户上传内容。健康检查、日志和 API 响应也不得输出这些完整路径。

## 7. 迁移原数据库到正式目录

以下操作必须在服务停止时执行。源数据库为：

```text
D:\文档存储\backend\script_materials.db
```

先确认原库存在、记录大小与 SHA-256，并制作不可替代的迁移前备份：

```powershell
$ErrorActionPreference = 'Stop'
$sourceDb = 'D:\文档存储\backend\script_materials.db'
$productionDb = 'D:\script_material_data\database\script_materials.db'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$preMigration = "D:\script_material_data\backups\pre_migration_$stamp"

if (-not (Test-Path -LiteralPath $sourceDb -PathType Leaf)) {
    throw '原开发数据库不存在，停止部署。'
}
if (Test-Path -LiteralPath $productionDb) {
    throw '正式数据库已存在。禁止重跑复制步骤或覆盖现有正式数据。'
}
if (Test-Path -LiteralPath $preMigration) {
    throw '本次迁移前备份目录已存在，停止以避免覆盖。'
}

New-Item -ItemType Directory -Path $preMigration -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path (Split-Path -Parent $productionDb) -Force -ErrorAction Stop | Out-Null
Get-Item -LiteralPath $sourceDb | Select-Object FullName,Length,LastWriteTime
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceDb).Hash
Copy-Item -LiteralPath $sourceDb -Destination (Join-Path $preMigration 'script_materials.db') -ErrorAction Stop
$backupHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $preMigration 'script_materials.db')).Hash
if ($sourceHash -ne $backupHash) { throw '迁移前备份哈希不一致，停止部署。' }
Copy-Item -LiteralPath $sourceDb -Destination $productionDb -ErrorAction Stop
$productionHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $productionDb).Hash
if ($sourceHash -ne $productionHash) { throw '正式副本哈希不一致，停止部署。' }
[pscustomobject]@{SourceSHA256=$sourceHash;BackupSHA256=$backupHash;ProductionSHA256=$productionHash}
```

只有源文件与备份哈希一致后才能继续。不要移动、覆盖或删除原库。

然后仅迁移正式副本：

```powershell
cd D:\文档存储\backend
$ErrorActionPreference = 'Stop'
$productionEnv = 'D:\文档存储\backend\.env.production'
if (-not (Test-Path -LiteralPath $productionEnv -PathType Leaf)) {
    throw '缺少 .env.production，禁止执行迁移。'
}
@('DATABASE_URL','STORAGE_ROOT','MATERIAL_STORAGE_PATH','LOG_DIR','BACKUP_ROOT','TEMP_ROOT','FRONTEND_DIST','SERVE_FRONTEND','PYTHONOPTIMIZE') |
    ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
$env:APP_ENV = 'production'
$env:SETTINGS_ENV_FILE = $productionEnv

& 'D:\文档存储\deploy\windows\check_environment.bat' --skip-audit
if ($LASTEXITCODE -ne 0) { throw '迁移前生产环境或路径隔离检查失败。' }

& .\.venv\Scripts\alembic.exe upgrade head
if ($LASTEXITCODE -ne 0) { throw 'alembic upgrade head 失败。' }

& .\.venv\Scripts\alembic.exe current
if ($LASTEXITCODE -ne 0) { throw 'alembic current 执行失败。' }

& .\.venv\Scripts\python.exe -c "from alembic.config import Config; from alembic.script import ScriptDirectory; from sqlalchemy import create_engine,text; from app.core.config import settings; head=ScriptDirectory.from_config(Config('alembic.ini')).get_current_head(); e=create_engine(settings.database_url); c=e.connect(); current=c.execute(text('SELECT version_num FROM alembic_version')).scalar_one_or_none(); c.close(); e.dispose(); print(f'current={current} head={head}'); raise SystemExit(0 if current is not None and current==head else 1)"
if ($LASTEXITCODE -ne 0) { throw '数据库迁移版本与 Alembic head 不一致。' }

& .\.venv\Scripts\alembic.exe check
if ($LASTEXITCODE -ne 0) { throw 'alembic check 失败。' }

& .\.venv\Scripts\python.exe -c "from sqlalchemy import create_engine,text; from app.core.config import settings; e=create_engine(settings.database_url); c=e.connect(); result=c.execute(text('PRAGMA integrity_check')).scalar_one(); c.close(); e.dispose(); print(f'integrity={result}'); raise SystemExit(0 if result=='ok' else 1)"
if ($LASTEXITCODE -ne 0) { throw 'PRAGMA integrity_check 未返回 ok。' }

& .\.venv\Scripts\python.exe -c "from sqlalchemy import create_engine,text; from app.core.config import settings; e=create_engine(settings.database_url); c=e.connect(); materials=c.execute(text('SELECT COUNT(*) FROM materials')).scalar_one(); metrics=c.execute(text('SELECT COUNT(*) FROM genre_metrics')).scalar_one(); c.close(); e.dispose(); print(f'materials={materials} genre_metrics={metrics}'); raise SystemExit(0 if materials==31 and metrics==20 else 1)"
if ($LASTEXITCODE -ne 0) { throw '迁移后历史素材或定位数据数量不符合 31/20 基线。' }

& .\.venv\Scripts\python.exe -m app.tools.audit_data --fail-on-missing
if ($LASTEXITCODE -ne 0) { throw '只读数据审计失败或发现数据库引用的附件缺失。' }
```

必须确认：

- Alembic 为 `20260811_0004` 或当前发布所声明的 head。
- SQLite `PRAGMA integrity_check` 返回 `ok`。
- 原有 31 条素材与 20 条定位数据仍存在。
- 中文正常显示。
- 历史年龄、学历、趋势和“近30天”等值没有被错误改写。
- 无附件旧素材被审计为无附件，而不是自动删除。

迁移报告应记录源/备份/正式副本哈希、迁移前后版本、数据数量、完整性检查和审计摘要，但不得记录附件正文。

## 8. 归档 Sprint 3 验收资产

下列内容只属于验收，不得合并到正式数据库或正式附件目录：

```text
D:\文档存储\script_materials_sprint3_runtime.db
D:\文档存储\sprint3_storage
```

管理员确认后，将其复制到 `D:\script_material_data\backups\sprint3_acceptance` 并保留原件，记录哈希和日期。正式配置不得指向该目录，除非管理员明确启动独立验收实例。

## 9. 环境检查与生产启动

```powershell
cd D:\文档存储
& .\deploy\windows\check_environment.bat
if ($LASTEXITCODE -ne 0) { throw '生产环境检查失败。' }
& .\deploy\windows\start_production.bat
if ($LASTEXITCODE -ne 0) { throw '生产服务启动失败。' }
```

启动脚本会检查虚拟环境、正式配置、数据库、storage 写入、前端 dist 和端口，并强制生产参数为 `0.0.0.0:8000`、`API_PREFIX=/api`、`DEBUG=false`、`SERVE_FRONTEND=true` 及指定 `frontend/dist`。随后执行 `alembic upgrade head`、`alembic check` 和缺失附件阻断审计，最后以单 worker 启动 Uvicorn。不要自行增加 `--reload` 或多个 worker。

启动后检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/health/ready
```

正式入口：

```text
http://服务器内网IP:8000/materials
http://服务器内网IP:8000/genre-map
http://服务器内网IP:8000/docs
```

直接刷新 `/materials`、`/genre-map`、`/settings/modules` 和一个 `/genres/:slug` 路由都应正常返回前端，未知 `/api/*` 必须返回 API 404。

## 10. Windows 防火墙

先获取企业批准的网段，例如 `10.20.0.0/16`。使用管理员 PowerShell 创建仅 Domain/Private 生效的入站规则：

```powershell
New-NetFirewallRule `
  -DisplayName '剧本素材库-企业内网-8000' `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 8000 `
  -Action Allow `
  -Profile Domain,Private `
  -RemoteAddress '10.20.0.0/16'
```

把示例网段替换为企业实际网段。检查规则：

```powershell
Get-NetFirewallRule -DisplayName '剧本素材库-企业内网-8000' |
  Get-NetFirewallPortFilter
```

禁止：

- 使用 `-Profile Any` 或 `Public`。
- 使用 `-RemoteAddress Any`。
- 在路由器配置互联网端口转发。
- 在云安全组向 `0.0.0.0/0` 放行 8000。
- 用公网反向代理发布该系统。

同一局域网另一台电脑的访问测试和防火墙配置必须由管理员在目标网络实机完成，并记录访问电脑 IP、网络配置文件和测试时间。

## 11. 每日备份任务计划

先手工运行一次并确认成功：

```powershell
& 'D:\文档存储\deploy\windows\run_backup.bat'
if ($LASTEXITCODE -ne 0) { throw '首次正式备份或自动验证失败。' }
```

再用“任务计划程序”创建任务：

- 名称：`剧本素材库-每日备份`。
- 运行账户：对代码和正式数据目录有最小必要权限的服务账户。
- 触发器：每天业务低峰期至少一次；建议同时启用“错过计划后尽快运行”。
- 操作：程序 `C:\Windows\System32\cmd.exe`，参数 `/c "D:\文档存储\deploy\windows\run_backup.bat"`。
- 起始于：`D:\文档存储`。
- 条件：服务器使用电源时按企业策略配置，不应因无人登录而跳过。
- 失败处理：记录非零退出码，并接入企业告警或由值班人员每日核对。

任务完成不等于备份可恢复。至少每月执行一次 `docs/BACKUP_RESTORE.md` 中的恢复到测试目录演练。

## 12. 发布后最低验收

1. readiness 全部为可用状态。
2. 页面和 API 均只请求当前 8000 端口，不请求 5173。
3. 素材上传、预览、下载、修改和物理删除正常。
4. 定位数据新增、编辑、Excel/CSV 导入导出正常。
5. 服务重启后数据保留。
6. `application.log` 和 `error.log` 可写且不包含文件正文或环境变量内容。
7. 正式备份生成、验证通过，并完成一次测试目录恢复演练。
8. 浏览器控制台无未处理 error/warn，后端无未处理异常。
9. 内网另一台电脑可访问，Public 网络和企业网段外访问被拒绝。

完整上线检查见 `docs/RELEASE_CHECKLIST.md`。
