# Linux 宝塔生产部署设计

## 1. 目标

为模块化剧本题材素材库增加一套与现有 Windows 部署并存的 Linux 生产部署方式，适配 Alibaba Cloud Linux 4 和宝塔 Nginx。部署必须保留现有 SQLite 数据库与附件，应用仅监听服务器回环地址，由 Nginx 提供公网 HTTP/HTTPS 入口。

本方案的固定部署布局为：

```text
/www/wwwroot/jubenku/          # GitHub 代码与前端构建产物
/www/server/data/jubenku/      # 独立正式数据根目录
├── database/
├── storage/
│   └── materials/
├── logs/
├── backups/
└── temp/
```

应用监听 `127.0.0.1:8100`，公网仅开放 `80` 和 `443`。SQLite 生产服务固定使用一个 worker。

## 2. 非目标

- 不修改或删除现有 Windows `.bat` 启动与部署文件。
- 不把 SQLite、用户附件、日志或真实 `.env.production` 提交到 Git。
- 不在启动脚本中安装系统软件、修改宝塔配置或修改云安全组。
- 不开放 `8100` 到公网。
- 不在本次工作中增加应用登录或权限系统。由于应用当前没有登录功能，正式站点仍需通过宝塔访问限制、IP 白名单或其他网络边界限制访问。

## 3. 交付文件

### `deploy/linux/start_production.sh`

主生产启动脚本，职责如下：

1. 使用脚本自身位置解析项目根目录，不依赖当前工作目录。
2. 启用严格 Shell 模式并设置安全文件权限掩码。
3. 固定从 `backend/.env.production` 读取生产配置。
4. 检查 Linux 虚拟环境、Alembic、生产配置和 `frontend/dist/index.html`。
5. 通过项目配置模型验证运行环境，而不是使用 Shell 解析 `.env`。
6. 拒绝以下不安全或不一致配置：
   - 非 `production` 环境；
   - 开启 `DEBUG`；
   - 后端监听非回环地址；
   - 未启用前端静态托管；
   - SQLite 数据库、storage、日志、备份或临时目录不是绝对路径；
   - 正式数据位于代码目录内；
   - 数据目录之间发生错误嵌套；
   - 数据库不存在、关键目录不可写或前端构建缺失；
   - 配置端口已经被其他进程监听。
7. 顺序执行：
   - `alembic upgrade head`；
   - `alembic check`；
   - `python -m app.tools.audit_data --fail-on-missing`。
8. 从配置模型读取最终主机和端口，使用 `exec` 启动单 worker Uvicorn，使 systemd 能正确接收进程状态和停止信号。
9. 任何检查、迁移或数据审计失败时立即退出，禁止带病启动。

脚本不自动创建或覆盖正式数据库。首次恢复数据必须在脚本运行前完成。

### `deploy/linux/jubenku.service`

systemd 服务模板：

- 使用 `www` 账户运行应用；
- 工作目录为 `/www/wwwroot/jubenku/backend`；
- 执行 `deploy/linux/start_production.sh`；
- 失败后自动重启，正常人工停止时不循环拉起；
- 设置合理的启动超时和停止超时；
- 不在服务文件中保存数据库路径、密码或其他生产配置；
- 日志主要由应用写入配置的轮转日志，systemd journal 保留启动与崩溃信息。

### `backend/.env.production.linux.example`

提供不含秘密的 Linux 配置模板：

```env
APP_ENV=production
APP_HOST=127.0.0.1
APP_PORT=8100
DEBUG=false

DATABASE_URL=sqlite:////www/server/data/jubenku/database/script_materials.db
STORAGE_ROOT=/www/server/data/jubenku/storage
LOG_DIR=/www/server/data/jubenku/logs
BACKUP_ROOT=/www/server/data/jubenku/backups
TEMP_ROOT=/www/server/data/jubenku/temp

SERVE_FRONTEND=true
FRONTEND_DIST=/www/wwwroot/jubenku/frontend/dist
CORS_ALLOWED_ORIGINS=
```

其他容量、保留期限、SQLite 和日志轮转参数沿用现有生产模板。

### `docs/LINUX_DEPLOYMENT.md`

面向首次使用宝塔的操作说明，包含：

- 安装或检查 Git、Python、Node.js 和 pnpm；
- 从 GitHub 克隆代码；
- 在 Linux 重新创建 Python 虚拟环境并安装依赖；
- 在 Linux 重新安装前端依赖并构建 `dist`；
- 创建独立数据目录和 `www` 用户权限；
- 从本机一致性备份恢复数据库与 `storage/materials`；
- 创建 `.env.production`；
- 手工运行启动脚本完成首次验证；
- 安装、启用和检查 systemd 服务；
- 在宝塔站点中把域名反向代理到 `http://127.0.0.1:8100`；
- 配置 HTTPS、访问限制以及仅开放 `80/443`；
- 更新、备份、回滚、查看日志和常见故障排查。

## 4. 数据迁移设计

当前确认的源数据为：

```text
.runtime/portable/database/script_materials.db
.runtime/portable/storage/materials/
```

迁移前基线为：

- Alembic 版本：`20260812_0009`；
- 素材：84 条；
- 项目：3 个；
- 标签：47 个；
- 上传平台：12 个；
- 数据库附件引用：17 个；
- 实际附件：17 个；
- 缺失附件：0 个。

迁移流程：

1. 停止本机便携服务，形成明确停机窗口。
2. 使用项目备份工具创建 SQLite 与附件一致性备份。
3. 校验备份结构和哈希后压缩备份目录。
4. 使用宝塔文件管理上传压缩包，不上传 Windows `.venv` 或 `node_modules`。
5. 在服务器临时目录解压并校验，不直接覆盖正式目录。
6. 首次部署时把数据库和附件复制到新建的正式数据目录。
7. 设置正式数据所有者为 `www`，目录仅向运行账户开放必要权限。
8. 运行迁移、数据审计和数量核对。
9. 验证通过后启动 systemd 服务，再配置 Nginx 入口。

如果服务器正式目录已经存在数据，恢复流程必须停止并要求人工确认，不能自动覆盖。

## 5. 请求流与网络边界

```text
浏览器
  → 云安全组 TCP 80/443
  → 宝塔 Nginx（域名与 HTTPS）
  → http://127.0.0.1:8100
  → FastAPI（API + frontend/dist）
  → /www/server/data/jubenku 下的 SQLite 与附件
```

云安全组和宝塔防火墙均不添加 `8100` 入方向规则。Nginx 保留上传体积限制和必要的代理头，并为长耗时上传设置明确超时。应用不信任来自公网的直连请求，因为公网无法路由到回环地址。

## 6. 更新与回滚

正常更新顺序：

1. 创建正式数据一致性备份并验证。
2. 记录当前 Git 提交哈希。
3. 拉取新代码。
4. 更新 Python 和前端依赖并重新构建前端。
5. 重启 systemd 服务，由启动脚本执行迁移和数据审计。
6. 检查 readiness、页面和日志。

如果启动失败，服务保持停止状态。管理员先查看 journal 和应用日志；代码可回退到上一提交，但数据库迁移回滚必须遵循迁移与备份恢复流程，不能直接删除或覆盖正式数据库。

## 7. 错误处理

- 所有 Shell 步骤检查退出码，错误信息说明失败位置和下一步处理方向。
- 日志和错误信息不输出 `.env.production` 内容，不回显敏感配置。
- 数据库不存在时拒绝启动，而不是自动创建空库。
- 附件引用缺失时数据审计失败并拒绝启动。
- 端口占用时拒绝启动并显示检查命令。
- Nginx 返回 502 时，排查顺序为 systemd 状态、journal、应用日志、回环端口和 readiness。

## 8. 测试与验收

实现采用脚本行为测试，而不是只检查源文件文本。测试使用临时项目布局和替身可执行文件，验证：

- 脚本能从任意当前目录解析项目根目录；
- 缺少虚拟环境、配置、前端构建或数据库时失败；
- 非生产、debug、非回环监听和数据目录位于代码内时失败；
- 迁移、Alembic 检查或数据审计任一步失败都会阻止 Uvicorn；
- 成功路径按照固定顺序执行检查，并以一个 worker 启动配置的 `127.0.0.1:8100`；
- systemd 单元能通过 `systemd-analyze verify` 时执行该验证；环境没有 systemd 时进行结构检查并明确说明限制；
- 后端全量测试、前端单元测试、类型检查和生产构建继续通过；
- `shellcheck` 可用时必须通过；不可用时至少运行 `bash -n` 和行为测试。

服务器最终验收：

- systemd 服务为 `active (running)`；
- `127.0.0.1:8100` 正在监听，公网无法直接访问该端口；
- readiness 返回 ready；
- 域名 HTTPS 可访问；
- 数据基线数量一致，17 个附件均可读取；
- 重启服务器后服务自动恢复；
- 备份命令可生成并验证新备份。
