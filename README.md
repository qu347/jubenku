# 模块化剧本题材素材库 v1.0.0

面向企业内部内容团队的素材管理与题材定位 Web 应用。系统提供真实文件上传、组合筛选、受控预览与下载、题材配置、年龄—学历气泡图，以及定位数据的 Excel/CSV 导入导出。

本项目是单一企业内部实例，没有登录和应用权限功能。任何能够访问服务地址的人都可以上传、修改和删除素材，因此生产部署必须依赖企业内网、Windows 防火墙和指定网段访问控制，禁止直接暴露到公网。

## V1.0 范围

最终业务页面只有：

| 路径 | 功能 |
| --- | --- |
| `/materials` | 企业素材上传、筛选、预览、编辑、下载和物理删除 |
| `/genre-map` | 年龄—学历气泡图、定位数据 CRUD、Excel/CSV 导入导出 |
| `/settings/modules` | 题材模块和功能板块配置 |
| `/genres/:slug` | 参数化题材页面 |
| `/` | 重定向到 `/materials` |

固定导航包含“素材库”“题材定位图”“题材配置”。页面数据全部来自后端 API，不使用前端 Mock 业务数据。

明确不包含：

- 登录、注册、会员、订阅和支付。
- 角色权限、多租户和多人协作。
- AI 生成、AI 改写、智能推荐和网页采集。
- 剧本项目、人物关系和知识图谱。
- 复杂素材版本、版本回滚和业务回收站。
- 复杂 Office 在线编辑或预览。

历史数据库中为迁移兼容保留的旧表，不代表 V1.0 提供对应页面或接口。

## 核心能力

### 企业素材库

- 单文件或多文件上传；每个文件独立返回成功或失败结果。
- 支持 PDF、DOCX、XLSX、CSV、TXT、Markdown、JPG、JPEG、PNG。
- 默认单文件上限 100MB，可通过生产配置调整。
- 按关键词、题材、素材类型、文件类型、标签、来源和上传时间组合筛选。
- 图片、TXT、Markdown 和 PDF 基础预览；Office 文件下载后本地打开。
- 只允许通过 Material ID 下载，不接收客户端文件系统路径。
- 服务端使用 UUID 文件名，数据库只保存相对路径。
- 素材删除同步清理受控目录内的物理附件，并保留二次确认。
- 兼容没有物理附件的旧素材，明确显示“无附件”。

### 题材定位

- 以平均年龄为横轴、学历层级为纵轴、用户占比为气泡大小。
- 颜色表示学历层级，描边表示重点题材。
- 支持平台、频道、周期、年龄、学历、趋势、重点状态和热度筛选。
- 新增、查看、编辑和软删除定位数据。
- Excel/CSV 模板下载、逐行校验导入、失败行明细和当前筛选结果导出。

### 题材配置

- 动态题材导航和 `/genres/:slug` 参数化页面。
- 题材模块新增、编辑、启停、显示、排序、复制和软删除。
- 功能板块新增、编辑、启停、排序和软删除。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Vue Router、Pinia、Element Plus、Apache ECharts、pnpm。
- 后端：Python、FastAPI、SQLAlchemy 2、Pydantic 2、Alembic、openpyxl。
- 数据库：V1.0 开发和生产均使用 SQLite。
- 生产托管：FastAPI 同时提供 `/api/*`、前端静态资源和 Vue Router SPA 回退。
- 运维：readiness、轮转日志、只读数据审计、SQLite 一致性备份及恢复验证。

SQLite 适合当前轻量内部部署。正式 Uvicorn 固定一个 worker，不使用 `--reload`；若未来出现大量人员持续并发上传和修改，再单独评估 PostgreSQL，V1.0 不实施数据库迁移。

## 主要 API

### 健康检查

```text
GET /api/health
GET /api/health/ready
```

### 题材模块与板块

```text
GET/POST       /api/genre-modules
GET/PATCH/DELETE /api/genre-modules/{id}
GET            /api/genre-modules/slug/{slug}
POST           /api/genre-modules/{id}/duplicate
POST           /api/genre-modules/{id}/enable
POST           /api/genre-modules/{id}/disable
PATCH          /api/genre-modules/batch/reorder
GET/POST       /api/genre-modules/{id}/sections
GET/PATCH/DELETE /api/module-sections/{id}
POST           /api/module-sections/{id}/enable
POST           /api/module-sections/{id}/disable
PATCH          /api/module-sections/batch/reorder
```

### 企业素材

```text
POST   /api/materials/upload
GET    /api/materials
GET    /api/materials/{id}
PATCH  /api/materials/{id}
DELETE /api/materials/{id}
GET    /api/materials/{id}/download
```

### 题材定位数据

```text
GET/POST       /api/genre-metrics
GET/PATCH/DELETE /api/genre-metrics/{id}
GET            /api/genre-metrics/import-template
POST           /api/genre-metrics/import
GET            /api/genre-metrics/export
```

交互式 API 文档默认位于 `/docs`。

## 本地开发

后端：

```powershell
cd D:\文档存储\backend
& python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

$devRoot = 'D:\文档存储\.runtime\development'
New-Item -ItemType Directory -Path $devRoot -Force | Out-Null
Remove-Item Env:SETTINGS_ENV_FILE -ErrorAction SilentlyContinue
$env:APP_ENV = 'development'
$env:DATABASE_URL = 'sqlite:///D:/文档存储/.runtime/development/script_materials.db'
$env:STORAGE_ROOT = 'D:/文档存储/.runtime/development/storage'
$env:MATERIAL_STORAGE_PATH = 'D:/文档存储/.runtime/development/storage/materials'
$env:LOG_DIR = 'D:/文档存储/.runtime/development/logs'
$env:BACKUP_ROOT = 'D:/文档存储/.runtime/development/backups'
$env:TEMP_ROOT = 'D:/文档存储/.runtime/development/temp'

& .\.venv\Scripts\alembic.exe upgrade head
if ($LASTEXITCODE -ne 0) { throw '独立开发数据库迁移失败。' }
& .\.venv\Scripts\python.exe -m app.seed.run
if ($LASTEXITCODE -ne 0) { throw '独立开发数据库初始化失败。' }
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd D:\文档存储\frontend
pnpm install --frozen-lockfile
pnpm run dev
```

开发入口为 `http://127.0.0.1:5173`，Vite 将相对 `/api` 请求代理到后端。上述命令把数据库、上传、日志和临时文件隔离在已忽略的 `.runtime/development`。

`backend/script_materials.db` 是必须保留的原始 0003 数据库。禁止对它直接执行 `alembic upgrade head`、seed 或开发写入；正式迁移只能按 [Windows 生产部署](docs/DEPLOYMENT.md) 的“先备份、复制正式副本、再迁移”流程执行。

## 测试与构建

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
.\.venv\Scripts\alembic.exe check

cd D:\文档存储\frontend
pnpm run type-check
pnpm run test:unit
pnpm run build
```

测试必须使用临时数据库和临时目录，不得写入正式数据根。

## Windows 生产部署

代码和正式数据严格分离：

```text
代码：D:\文档存储
数据：D:\script_material_data
```

生产配置复制自 `backend/.env.production.example`，正式的 `backend/.env.production` 不进入版本控制。生产前端先构建到 `frontend/dist`，再由 FastAPI 从 8000 端口托管；正式环境不运行 5173。

部署脚本：

```powershell
D:\文档存储\deploy\windows\check_environment.bat
D:\文档存储\deploy\windows\start_production.bat
D:\文档存储\deploy\windows\run_backup.bat
```

脚本固定读取正式配置，拒绝继承到验收或临时数据路径，校验数据库、storage、日志、备份和临时目录隔离，并强制 `0.0.0.0:8000`、`/api`、非调试模式及指定生产前端。生产启动执行 Alembic 迁移、模型检查和 `--fail-on-missing` 只读审计，任一失败都会阻止启动。

生产入口形态：

```text
http://企业服务器内网IP:8000/materials
http://企业服务器内网IP:8000/genre-map
```

只允许 Windows 防火墙 Domain/Private 配置文件中的指定企业网段访问 8000。禁止 Public 规则、互联网端口转发、路由器公网映射或公网反向代理。

## 数据保护

- 正式数据库、上传附件、日志和备份位于代码目录之外，应用升级不得覆盖。
- 数据审计默认只读，统计无附件旧素材、缺失附件和孤立文件，不自动删除。
- 正式备份使用 SQLite Backup API，并逐项校验数据库完整性、manifest、文件数量、大小和 SHA-256。
- 删除素材是物理删除；重要资料依赖每日备份恢复。
- 恢复必须先停止服务、保护当前现场、验证目标备份，并恢复到全新的临时目录演练；禁止在运行中覆盖正式数据库。

## 文档

- [产品规格](docs/PRODUCT_SPEC.md)
- [Sprint 4 范围](docs/SPRINT_4.md)
- [用户使用说明](docs/USER_GUIDE.md)
- [Windows 生产部署](docs/DEPLOYMENT.md)
- [日常运维](docs/OPERATIONS.md)
- [备份与恢复](docs/BACKUP_RESTORE.md)
- [发布检查表](docs/RELEASE_CHECKLIST.md)

正式上线前必须完成发布检查表中的数据库迁移、完整性、审计、备份验证、恢复演练和局域网防火墙验收。
