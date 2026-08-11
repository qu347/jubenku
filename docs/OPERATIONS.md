# 生产运行与运维手册

## 1. 运行基线

- 代码：`D:\文档存储`。
- 正式数据：`D:\script_material_data`。
- 正式端口：8000。
- 生产进程：FastAPI/Uvicorn，SQLite 固定 1 个 worker，不使用 `--reload`。
- 生产页面和 API：同一 8000 端口；不运行 5173。
- 网络：只允许 Domain/Private 企业网段，禁止公网。

系统没有登录和权限。任何能访问服务地址的人都能上传、修改和删除素材；网络规则异常应按安全事件处理。

## 2. 日常启动与停止

### 启动前检查

```powershell
cd D:\文档存储
& .\deploy\windows\check_environment.bat
if ($LASTEXITCODE -ne 0) { throw '生产环境检查失败。' }
```

检查不通过时不要跳过。修复虚拟环境、配置、数据库、storage、dist 或端口问题后重试。

### 启动

```powershell
& 'D:\文档存储\deploy\windows\start_production.bat'
if ($LASTEXITCODE -ne 0) { throw '生产服务启动失败。' }
```

脚本先迁移到 head 并执行 `alembic check`，然后单 worker 启动。启动成功后检查 readiness。

### 停止

- 前台运行：在启动窗口按 `Ctrl+C`，等待进程正常退出。
- 任务计划运行：在任务计划程序中停止该应用任务。
- Windows 服务包装运行：使用该服务管理器停止指定服务。

不要使用“结束所有 Python/Node 进程”的命令；同一服务器可能运行其他业务。停止后用以下命令确认 8000 不再监听：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
```

## 3. 健康检查

基础健康：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

生产就绪：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health/ready
```

readiness 只返回：`status`、`database`、`migration`、`storage`、`frontend`、`timestamp`。它检查数据库简单查询、Alembic head、storage 存在和可写、生产 dist 存在。返回中不应出现数据库路径、storage 路径、系统用户名或环境变量。

建议每 5 分钟由企业监控访问 readiness。连续失败时告警，但不要把响应转发到公网监控平台。

## 4. 日志查看

正式日志目录：

```text
D:\script_material_data\logs\application.log
D:\script_material_data\logs\error.log
```

查看最近内容：

```powershell
Get-Content 'D:\script_material_data\logs\application.log' -Tail 100
Get-Content 'D:\script_material_data\logs\error.log' -Tail 100
```

实时跟踪：

```powershell
Get-Content 'D:\script_material_data\logs\application.log' -Tail 20 -Wait
```

日志会轮转。上传、删除、导入等操作记录业务 ID、结果和失败类型，不记录文件正文；未处理异常进入 `error.log`。发现绝对服务器路径、环境变量内容、文件正文或浏览器收到 traceback 时，应停止发布并按缺陷处理。

## 5. 每日数据审计

```powershell
& 'D:\文档存储\deploy\windows\check_environment.bat' --allow-running
if ($LASTEXITCODE -ne 0) {
    throw '生产环境检查或只读数据审计失败。'
}
```

正式日常审计统一通过上述加固脚本执行。脚本固定读取 `.env.production`、清除调用终端中的路径覆盖，并在读取数据库或 storage 前校验所有正式路径以及 `0.0.0.0:8000`、`/api`、生产前端和非调试模式等固定运行参数。`audit_data --json` 只用于显式传入临时数据库和临时素材根目录的自动化测试，不作为正式运维命令。

审计只读，输出：

- 素材总数。
- 有附件素材数。
- 无附件旧素材数。
- 数据库记录存在但文件缺失数。
- storage 中数据库无记录的孤立文件数。
- 定位数据数。

审计不会自动删除或修复。缺失文件或孤立文件从 0 增长时：暂停相关批量操作，保存审计输出，检查应用/error 日志与最近备份。未经确认不得手工删除文件或数据库记录。

## 6. 每日备份与验证

```powershell
& 'D:\文档存储\deploy\windows\run_backup.bat'
if ($LASTEXITCODE -ne 0) { throw '正式备份或自动验证失败。' }
```

脚本成功退出后仍需记录生成的备份目录。抽查或恢复前再次显式验证：

```powershell
cd D:\文档存储\backend
$backupDirectory = 'D:\script_material_data\backups\YYYYMMDD_HHMMSS'
& .\.venv\Scripts\python.exe -m app.tools.verify_backup $backupDirectory
if ($LASTEXITCODE -ne 0) { throw '指定备份验证失败。' }
```

每日检查任务计划程序的最后运行结果和 `backup.log`。非 0 退出码、缺少 manifest、完整性检查失败或文件数量不一致都视为备份失败。

至少每天备份一次，每月按 `docs/BACKUP_RESTORE.md` 恢复到独立测试目录。物理删除前、批量导入前、代码升级前和迁移前建议额外备份。

## 7. 恢复流程

正式恢复不能在本手册中简化执行。必须完整遵循 `docs/BACKUP_RESTORE.md`：

1. 停止服务。
2. 备份现场。
3. 验证目标备份。
4. 恢复到新临时目录。
5. 完整性、版本、审计和临时实例验收。
6. 业务批准后切换。
7. 启动并完成恢复后检查。

禁止在服务运行时复制备份数据库覆盖正式数据库。

## 8. 应用升级流程

1. 阅读发布说明，确认没有超出 V1.0 冻结范围的业务变更。
2. 检查磁盘空间与当前 readiness。
3. 运行后端测试、前端测试、类型检查和生产构建。
4. 执行正式备份并验证。
5. 运行数据审计并保存结果。
6. 停止服务并确认 8000 端口释放。
7. 更新代码，但不覆盖 `D:\script_material_data` 和 `backend\.env.production`。
8. 重新安装后端依赖：

   ```powershell
   cd D:\文档存储\backend
   & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   if ($LASTEXITCODE -ne 0) { throw '后端依赖安装失败。' }
   ```

9. 重新构建前端：

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

10. 使用加固脚本执行迁移前检查。它只接受固定正式路径，并会拒绝继承调用终端中的数据库或 storage 覆盖：

    ```powershell
    & 'D:\文档存储\deploy\windows\check_environment.bat' --skip-audit
    if ($LASTEXITCODE -ne 0) { throw '升级前生产环境检查失败。' }
    ```

11. 使用 `start_production.bat` 启动。脚本内部逐项执行 Alembic upgrade/check 和 `--fail-on-missing` 数据审计，任何一步失败都会阻止服务启动：

    ```powershell
    & 'D:\文档存储\deploy\windows\start_production.bat'
    if ($LASTEXITCODE -ne 0) { throw '生产启动或迁移失败。' }
    ```
12. 检查 readiness、前端直接刷新、核心业务、日志和浏览器控制台。
13. 观察期内保留升级前备份；回退也必须先恢复到临时目录验证。

不得重写 0001、0003、0004 等历史迁移，不得使用 `create_all` 代替 Alembic。

## 9. SQLite 运行说明

- 当前规模采用 SQLite 适合轻量企业内部部署。
- 每个数据库连接启用 `foreign_keys` 和合理的 `busy_timeout`。
- WAL 由 `SQLITE_WAL_ENABLED` 配置；备份仍使用 SQLite Backup API，不能直接复制正在写入的 db/WAL 文件冒充一致性备份。
- Uvicorn 固定单 worker，避免多个进程争用同一 SQLite 文件。
- 当大量人员持续同时上传、修改和导入，锁等待频繁或单机磁盘成为瓶颈时，再立项评估 PostgreSQL；Sprint 4 不做数据库迁移。

## 10. 常见故障排查

### 服务无法启动

1. 运行 `check_environment.bat`。
2. 查看 `error.log`。
3. 检查 `.env.production` 是否存在，但不要把内容发到聊天或工单。
4. 检查 `frontend\dist\index.html`。
5. 检查数据库/storage/logs/temp 的权限和剩余磁盘空间。

### 8000 端口被占用

```powershell
$listeners = Get-NetTCPConnection -LocalPort 8000 -State Listen
$listeners | Select-Object LocalAddress,LocalPort,OwningProcess
if ($listeners) {
    Get-Process -Id $listeners.OwningProcess
}
```

确认进程归属后只停止目标服务。不要盲目强制结束未知进程。

### readiness 的 database 或 migration 失败

- 停止写操作。
- 执行 `alembic current` 和 `alembic check`。
- 对数据库执行完整性检查或验证最近备份。
- 不要用空数据库替换正式库，也不要运行 seed 清空/覆盖数据。

### SQLite 提示 locked/busy

- 确认只有一个生产 worker、没有第二个生产实例或数据库 GUI 正在写入。
- 等待当前上传/导入事务完成后重试。
- 检查 busy timeout 配置和磁盘响应。
- 若持续发生，保存日志并评估并发规模，而不是启动更多 worker。

### storage 不可写

- 检查磁盘空间、目录权限和安全软件拦截。
- 确认 `STORAGE_ROOT` 位于正式数据目录且不是代码目录。
- 不要临时改到桌面、用户目录或 Sprint 3 验收目录。

### 记录存在但文件缺失

- 不要删除记录掩盖问题。
- 运行只读审计，记录 Material ID 和时间。
- 验证最近备份，在临时目录确认文件可恢复后再按正式恢复流程处理。
- API 的 404 不应包含服务器绝对路径。

### 前端路由刷新 404 或返回 API 页面

- 确认 `SERVE_FRONTEND=true` 和 dist 完整。
- 确认通过 8000 访问，不是 5173。
- `/api/*` 404 是 API 行为；非 API 页面路由应回退到 `index.html`。

### 局域网其他电脑无法访问

- 先在服务器访问 `127.0.0.1:8000`。
- 确认监听地址是 `0.0.0.0`。
- 检查 Windows 当前网络为 Domain 或 Private，而非 Public。
- 检查防火墙远程网段是否包含访问电脑 IP。
- 不要通过公网端口映射“临时解决”。

## 11. 日常记录建议

值班记录至少包含：日期、readiness、审计摘要、备份目录、验证结果、日志异常、磁盘余量和处理人。发布、迁移、恢复、防火墙变更必须双人复核并保留操作时间和结果。
