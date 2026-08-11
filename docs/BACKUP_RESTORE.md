# 备份、验证与恢复说明

## 1. 重要原则

素材删除会同时删除数据库记录和物理附件，正式部署必须依赖可验证备份。备份只有在 `verify_backup` 返回成功后才算可用。

恢复属于高风险运维操作，必须遵守：

1. 停止生产服务。
2. 再次备份当前现场，不因“现场可能有问题”而跳过。
3. 验证目标备份。
4. 先恢复到独立临时目录。
5. 对临时数据库执行 `PRAGMA integrity_check` 并检查 Alembic 版本。
6. 对临时数据库和临时 storage 执行只读审计。
7. 使用临时端口启动恢复演练实例。
8. 验证通过后，取得业务负责人批准，再切换正式目录。
9. 绝不在服务运行时覆盖正式数据库。

恢复会把数据回退到备份时间点，备份之后的修改、上传和删除可能丢失。开始正式切换前必须明确恢复点和业务影响。

## 2. 生成正式备份

正式环境只允许使用经过路径隔离校验的安全脚本：

```powershell
& 'D:\文档存储\deploy\windows\run_backup.bat'
if ($LASTEXITCODE -ne 0) { throw '正式备份或自动验证失败。' }
```

底层 CLI 只用于自动化测试或一次性隔离目录，必须显式提供全部数据路径，不得作为正式备份的替代命令：

```powershell
cd D:\文档存储\backend
& .\.venv\Scripts\python.exe -m app.tools.backup `
  --database-url 'sqlite:///D:/test/database/script_materials.db' `
  --materials-root 'D:\test\storage\materials' `
  --backup-root 'D:\test\backups' `
  --retention-days 30
if ($LASTEXITCODE -ne 0) { throw '隔离测试备份失败。' }
```

正式备份目录格式（时间戳使用 UTC；manifest 中记录带时区的 ISO 8601 UTC 时间）：

```text
D:\script_material_data\backups\YYYYMMDD_HHMMSS\
├─ database\script_materials.db
├─ storage\materials\
├─ manifest.json
└─ backup.log
```

数据库使用 SQLite Backup API 生成一致性副本；附件复制到该备份自己的 storage。manifest 记录备份时间、数据库 SHA-256、文件数量、总大小和逐文件校验信息。成功备份标记为 `status=complete` 且 `verification.status=passed`。备份过程失败时退出码非 0，失败目录保留 `status=failed` 的 manifest 和日志供排查，不会参与恢复成功判定或自动保留期清理。

## 3. 验证备份

对选定目录执行：

```powershell
cd D:\文档存储\backend
$backupDirectory = 'D:\script_material_data\backups\20260811_230000'
& .\.venv\Scripts\python.exe -m app.tools.verify_backup $backupDirectory
if ($LASTEXITCODE -ne 0) { throw '指定备份验证失败。' }
```

验证内容至少包括：

- `manifest.json` 存在、结构合法且状态正确。
- 备份数据库存在，SHA-256 与 manifest 一致。
- SQLite `PRAGMA integrity_check` 返回 `ok`。
- storage 文件数量、相对路径、大小与校验信息一致。
- manifest 声明的文件没有缺失，备份中没有被意外替换的文件。
- 活跃素材记录中的 `storage_path` 是安全相对路径，且在备份 storage 中存在；引用缺失文件或不安全路径会使验证失败。
- 孤立文件只在验证结果中报告，不会被备份或验证命令自动删除。

命令成功退出 0，失败退出 1。任何失败都必须阻止恢复。不要手工修改 manifest 来绕过校验。

需要机器可读输出时：

```powershell
$backupDirectory = 'D:\script_material_data\backups\20260811_230000'
& .\.venv\Scripts\python.exe -m app.tools.verify_backup $backupDirectory --json
if ($LASTEXITCODE -ne 0) { throw '指定备份验证失败。' }
```

## 4. 备份保留策略

- 默认 `BACKUP_RETENTION_DAYS=30`。
- 每天至少备份一次；关键批量导入、版本升级和数据库迁移前额外备份。
- 只有本次新备份验证成功后，备份工具才允许清理超过保留期、且本身具有验证通过标记的旧备份。
- 清理旧备份永远不得删除正式数据库或正式 storage。
- 至少保留一份离线或受限目录副本，避免同一磁盘故障同时损坏生产数据和备份。
- 每月最少执行一次恢复演练；重大升级前再执行一次。

## 5. 恢复到临时测试目录演练

这一演练不会覆盖正式数据，是每次发布验收和月度运维的强制项。

### 5.1 停止生产写入

正式恢复演练如果仅复制已完成备份，可以让生产继续运行；但为了完整模拟正式恢复和避免操作人员选错目录，发布验收期间建议先停止生产服务。通过前台启动时按 `Ctrl+C`；通过任务计划启动时用任务计划程序停止对应任务。不要结束所有 Python 进程。

### 5.2 保护当前现场

```powershell
& 'D:\文档存储\deploy\windows\run_backup.bat'
if ($LASTEXITCODE -ne 0) { throw '恢复前现场备份或自动验证失败。' }
```

记录新现场备份目录并立即验证。现场备份失败时停止恢复流程。

### 5.3 验证目标备份

```powershell
$backup = 'D:\script_material_data\backups\20260811_230000'
cd D:\文档存储\backend
if (-not (Test-Path -LiteralPath $backup -PathType Container)) {
    throw '目标备份目录不存在，停止恢复。'
}
& .\.venv\Scripts\python.exe -m app.tools.verify_backup $backup
if ($LASTEXITCODE -ne 0) { throw '目标备份验证失败，停止恢复。' }
```

### 5.4 复制到全新的测试目录

```powershell
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$drill = "D:\script_material_data\temp\restore_drill_$stamp"
$databaseDir = Join-Path $drill 'database'
$storageDir = Join-Path $drill 'storage'

if (Test-Path -LiteralPath $drill) {
    throw '恢复演练目标已存在，禁止合并或覆盖；请生成新的演练目录。'
}
New-Item -ItemType Directory -Path $drill -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $databaseDir,$storageDir -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath (Join-Path $backup 'database\script_materials.db') -Destination $databaseDir -ErrorAction Stop
Copy-Item -LiteralPath (Join-Path $backup 'storage\materials') -Destination $storageDir -Recurse -ErrorAction Stop
```

确认 `$drill` 是新建的 `temp\restore_drill_*` 目录，不得指向 `D:\script_material_data\database` 或正式 `storage`。

### 5.5 检查临时数据库与数据

```powershell
$drillDb = (Join-Path $databaseDir 'script_materials.db').Replace('\','/')
$drillMaterials = Join-Path $storageDir 'materials'
$drillUrl = "sqlite:///$drillDb"

& .\.venv\Scripts\python.exe -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); result=c.execute('PRAGMA integrity_check').fetchone()[0]; print(result); c.close(); raise SystemExit(0 if result=='ok' else 1)" (Join-Path $databaseDir 'script_materials.db')
if ($LASTEXITCODE -ne 0) { throw '演练数据库完整性检查失败。' }

$env:DATABASE_URL = $drillUrl
& .\.venv\Scripts\alembic.exe current
if ($LASTEXITCODE -ne 0) { throw '演练数据库 alembic current 执行失败。' }
& .\.venv\Scripts\python.exe -c "from alembic.config import Config; from alembic.script import ScriptDirectory; from sqlalchemy import create_engine,text; from app.core.config import settings; head=ScriptDirectory.from_config(Config('alembic.ini')).get_current_head(); e=create_engine(settings.database_url); c=e.connect(); current=c.execute(text('SELECT version_num FROM alembic_version')).scalar_one_or_none(); c.close(); e.dispose(); print(f'current={current} head={head}'); raise SystemExit(0 if current is not None and current==head else 1)"
if ($LASTEXITCODE -ne 0) { throw '演练数据库迁移版本与 Alembic head 不一致。' }
& .\.venv\Scripts\python.exe -m app.tools.audit_data `
  --database-url $drillUrl `
  --materials-root $drillMaterials `
  --fail-on-missing
if ($LASTEXITCODE -ne 0) { throw '演练数据审计失败或发现附件缺失。' }
```

必须确认完整性为 `ok`、Alembic 版本符合当前发布、素材和定位数据数量符合备份 manifest，且文件缺失/孤立文件没有异常增长。

### 5.6 用临时实例验证恢复数据

保持生产实例停止，或确认临时实例使用不同端口和全部临时路径：

```powershell
$env:APP_ENV = 'production'
$env:APP_HOST = '127.0.0.1'
$env:APP_PORT = '8100'
$env:DATABASE_URL = $drillUrl
$env:STORAGE_ROOT = $storageDir
$env:MATERIAL_STORAGE_PATH = $drillMaterials
$env:LOG_DIR = (Join-Path $drill 'logs')
$env:BACKUP_ROOT = (Join-Path $drill 'backups')
$env:TEMP_ROOT = (Join-Path $drill 'temp')
$env:SERVE_FRONTEND = 'true'
$env:FRONTEND_DIST = 'D:/文档存储/frontend/dist'

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --workers 1
```

访问 `http://127.0.0.1:8100/materials`，检查：

1. 素材列表、中文标题和无附件旧记录正常。
2. 选择若干有附件素材完成预览与下载。
3. 打开题材定位图，气泡和表格数量正常。
4. 导出 Excel 和 CSV，中文正常。
5. `/api/health/ready` 全部通过。
6. 浏览器控制台和临时日志没有未处理异常。

演练完成后按 `Ctrl+C` 停止 8100 实例，并清除本终端中覆盖用的环境变量或直接关闭终端。保留演练目录和记录直至发布验收完成；不要让生产配置指向演练目录。

### 5.7 演练记录

每次演练填写：

| 项目 | 记录 |
| --- | --- |
| 演练时间 |  |
| 操作人/复核人 |  |
| 目标备份目录 |  |
| 目标备份时间 |  |
| `verify_backup` 结果 |  |
| 临时恢复目录 |  |
| SQLite integrity_check |  |
| Alembic 版本 |  |
| 素材/定位数据数量 |  |
| 缺失文件/孤立文件数量 |  |
| 临时实例地址 |  |
| 页面与下载验收 |  |
| 结论与遗留问题 |  |

## 6. 正式恢复切换

只有临时演练全部通过、业务负责人确认恢复点后才能执行。

1. 停止生产服务并确认 8000 端口不再监听。
2. 再次运行正式备份并验证，作为恢复前现场保护。
3. 再次验证目标备份。
4. 将目标备份复制到新的 `temp\restore_candidate_*` 目录，重复完整性、版本和审计检查。
5. 在 `backups\pre_restore_hold_*` 创建现场保留目录。
6. 将当前正式数据库和 `storage\materials` 移入现场保留目录；不得删除。
7. 将候选数据库和候选 `materials` 复制到正式位置。
8. 对正式位置再次执行完整性检查、Alembic current 和只读审计。
9. 使用 `deploy\windows\start_production.bat` 启动。
10. 检查 readiness、上传、预览、下载、气泡图、Excel/CSV 导出及日志。
11. 在观察期结束前保留现场目录；回退时执行相同的停止、验证和临时演练流程。

切换时不要使用通配符、未展开的环境变量或递归删除命令。逐一核对源和目标的绝对路径，确保所有目标都位于 `D:\script_material_data` 内。

## 7. 恢复后验证清单

- [ ] 服务启动且 `/api/health/ready` 全部通过。
- [ ] 数据库版本为发布要求的 head。
- [ ] `PRAGMA integrity_check` 为 `ok`。
- [ ] 数据审计数量与目标备份一致。
- [ ] 无附件旧素材显示正常且不能下载。
- [ ] 有附件素材可预览和下载。
- [ ] 新上传文件进入正式 `storage\materials\YYYY\MM`。
- [ ] 删除测试素材后只清理受控目录内对应文件。
- [ ] 题材气泡图与定位表正常。
- [ ] Excel/CSV 导出中文正常。
- [ ] `application.log` 与 `error.log` 无未处理异常或路径泄露。
- [ ] 恢复时间、恢复点、现场备份和复核人已记录。
