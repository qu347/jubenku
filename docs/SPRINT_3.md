# Sprint 3 · 企业素材库与题材定位

## 目标

Sprint 3 是精简后的核心业务阶段，面向企业内部单实例使用，完成两条真实数据链路：

1. 企业文件上传、素材元数据维护、筛选、预览和下载。
2. 题材定位数据维护、CSV/Excel 导入导出，以及年龄—学历题材气泡图。

本轮延续 Sprint 1、Sprint 2 的架构与视觉，不重建前端，不删除或重写既有迁移，不使用前端 Mock 业务数据。

## 实施范围

### 企业素材库

- 单文件和多文件批量上传。
- 公共题材、素材类型、简单标签、来源和说明。
- 素材列表、分页、排序、组合筛选和关键词搜索。
- 素材详情与基础预览。
- 元数据编辑、受控下载和删除。
- 上传、保存、失败补偿及物理文件清理。

### 题材定位

- 定位数据新增、查看、修改、删除、筛选和分页。
- Excel/CSV 模板下载、逐行导入、失败明细和筛选结果导出。
- 年龄—学历题材气泡图。
- 图表与表格视图切换。
- 气泡详情及跳转到对应题材的素材筛选结果。

### 既有能力

- 保留 `/settings/modules` 的题材和功能板块配置。
- 保留 `/genres/:slug` 的参数化题材页面及动态题材导航。
- 复用现有 `Material` 与 `GenreMetric`，只做增量字段和迁移。

## 明确排除

本 Sprint 不实施：

- 登录、注册、账号体系。
- 会员、订阅和支付。
- 角色权限、多租户和多人协作。
- AI 生成、改写、推荐或自动分类。
- 网页抓取、自动采集和外部内容同步。
- 剧本项目、项目—素材关系和人物关系。
- 独立标签管理后台。
- 动态素材字段编辑器。
- `MaterialVersion`、`MaterialRelation`、`ProjectMaterial` 等复杂业务。
- 复杂版本管理、版本回滚和复杂回收站。
- 复杂 Office 在线预览。

已存在的旧模型可以保留，但本 Sprint 不为这些排除项新增接口、页面或业务依赖。

## 开始前基线检查

实施前运行现有后端测试、迁移检查、前端类型检查、单元测试和生产构建。若存在回归，先修复回归问题。

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
.\.venv\Scripts\alembic.exe check

cd D:\文档存储\frontend
pnpm run type-check
pnpm run test:unit
pnpm run build
```

## 数据模型

### Material

复用现有 `Material`，不得重复定义。根据当前模型增量补齐：

- `id`
- `genre_module_id`
- `title`
- `material_type`
- `description`
- `tags_json`
- `source`
- `original_filename`
- `stored_filename`
- `storage_path`
- `file_extension`
- `mime_type`
- `file_size`
- `created_at`
- `updated_at`
- `deleted_at`

规则：

- 一条素材记录对应一个上传文件。
- 多文件批量上传时，每个文件单独创建记录、提交结果和失败原因。
- `tags_json` 使用 SQLAlchemy JSON 保存简单字符串数组，不建设独立 Tag 管理系统。
- `title` 默认取原文件名去掉扩展名后的值。
- `PATCH` 只修改元数据，不替换物理文件，也不得修改服务器文件名、存储路径、大小或 MIME 类型。
- 如果需要新增字段，应新建 Sprint 3 Alembic 迁移，必须同时支持 `upgrade` 和 `downgrade`；不得修改旧迁移。

### GenreMetric

复用现有 `GenreMetric`，不得重复定义。确认或增量补齐：

- `id`
- `genre_module_id`
- `platform`
- `channel`
- `period`
- `average_age`
- `age_group`
- `education_level`
- `audience_share`
- `heat_index`
- `trend`
- `is_core`
- `sample_size`
- `data_source`
- `remark`
- `created_at`
- `updated_at`
- `deleted_at`

枚举与校验：

- `age_group`：`youth`、`middle`、`senior`。
- `education_level`：`low`、`medium`、`high`。
- `trend`：`rising`、`stable`、`falling`。
- `average_age`：大于 0 且小于等于 100。
- `audience_share`：0 至 100，包含边界。
- `heat_index`：0 至 100，包含边界。
- `sample_size`：大于等于 0。
- `period`：使用 `YYYY-MM`、`YYYY-Q1` 等明确格式。
- `genre_module_id` 必须关联存在且未删除的题材模块。
- 删除延续现有软删除规则，普通查询默认排除已删除记录。

## 文件存储与安全

### 存储规则

- 存储根目录：`backend/storage/materials/`。
- 按年月分目录：`backend/storage/materials/YYYY/MM/`。
- 服务器文件名使用 UUID，例如 `2026/08/550e8400-e29b-41d4-a716-446655440000.pdf`。
- 数据库只保存相对于存储根目录的路径，不保存 `D:\` 开头的绝对路径。
- 必须保留 `original_filename`，但不能使用原文件名决定服务器路径。
- 默认最大文件大小为 100MB，通过 `MAX_UPLOAD_MB=100` 配置。

允许扩展名：

- `.pdf`
- `.docx`
- `.xlsx`
- `.csv`
- `.txt`
- `.md`
- `.jpg`
- `.jpeg`
- `.png`

### 安全与一致性要求

1. 不信任原始文件名，阻止 `../`、绝对路径、分隔符和路径穿越影响存储目录。
2. 服务器文件名必须由 UUID 生成。
3. 同时校验扩展名、文件大小，并尽可能校验 MIME 类型与扩展名是否一致。
4. 上传失败时清理临时文件和未完成文件。
5. 文件落盘后数据库写入失败时删除已经保存的文件。
6. 多文件上传逐文件隔离，单文件失败不得回滚其他成功文件。
7. 删除素材时清理数据库记录和对应物理文件；物理文件不存在时仍允许清理数据库记录并返回明确结果。
8. 下载接口不得接受任何文件系统路径，只能通过 Material ID 查询并下载。
9. 读取或删除前，将数据库相对路径解析到存储根目录并校验最终路径仍位于根目录之内。
10. 下载响应使用原文件名，并设置正确的 `Content-Type`，但不得暴露服务器绝对路径。

## 后端接口

### 素材上传与管理

- `POST /api/materials/upload`
- `GET /api/materials`
- `GET /api/materials/{material_id}`
- `PATCH /api/materials/{material_id}`
- `DELETE /api/materials/{material_id}`
- `GET /api/materials/{material_id}/download`

`POST /api/materials/upload` 使用 `multipart/form-data`，参数包括：

- `files`
- `genre_module_id`
- `material_type`
- `tags`
- `source`
- `description`

上传响应必须包含成功数量、失败数量、每个文件的处理结果以及已创建的 Material 列表。失败文件不得留下数据库记录或物理文件。

`GET /api/materials` 支持：

- `keyword`
- `genre_module_id`
- `material_type`
- `file_extension`
- `tags`
- `source`
- `uploaded_from`
- `uploaded_to`
- `sort`
- `page`
- `page_size`

列表规则：

- `keyword` 搜索 `title`、`original_filename`、`description` 和 `source`。
- 不同筛选条件之间使用 AND。
- `tags` 多选默认匹配任一标签。
- 默认排除 `deleted_at` 非空记录。
- `sort` 支持 `created_desc`、`created_asc`、`updated_desc`、`updated_asc`、`title_asc`、`title_desc`、`file_size_desc` 和 `file_size_asc`。
- 分页响应包含 `items`、`total`、`page`、`page_size` 和 `pages`。

`PATCH /api/materials/{material_id}` 允许修改：

- `title`
- `genre_module_id`
- `material_type`
- `tags`
- `source`
- `description`

不得通过 `PATCH` 修改 `stored_filename`、`storage_path`、`file_size` 或 `mime_type`。

### 题材定位数据

- `GET /api/genre-metrics`
- `POST /api/genre-metrics`
- `GET /api/genre-metrics/{metric_id}`
- `PATCH /api/genre-metrics/{metric_id}`
- `DELETE /api/genre-metrics/{metric_id}`
- `GET /api/genre-metrics/import-template`
- `POST /api/genre-metrics/import`
- `GET /api/genre-metrics/export`

`GET /api/genre-metrics` 支持：

- `genre_module_id`
- `platform`
- `channel`
- `period`
- `age_group`
- `education_level`
- `trend`
- `is_core`
- `heat_min`
- `heat_max`
- `page`
- `page_size`

导入规则：

- 支持 `.xlsx` 和 `.csv`，Excel 使用 openpyxl 处理。
- 通过题材名称匹配 `GenreModule`；不存在的题材返回错误，不自动创建。
- 每一行独立校验，合法行正常写入，非法行不写入。
- 单行错误不得导致整个文件处理失败。
- 响应包含成功行数、失败行数、失败行号、失败字段和中文失败原因。

导入模板固定列名：

1. 题材
2. 数据平台
3. 频道
4. 数据周期
5. 平均年龄
6. 年龄层级
7. 学历层级
8. 用户占比
9. 热度指数
10. 趋势
11. 是否重点题材
12. 样本数量
13. 数据来源
14. 备注

导出规则：

- 按当前筛选条件导出。
- 支持 `.xlsx` 和 `.csv`。
- 默认文件名包含日期时间。
- CSV 应使用兼容 Excel 的 UTF-8 编码，中文不得乱码。

## 前端路由与导航

最终路由：

- `/`：重定向到 `/materials`。
- `/materials`：素材上传、筛选、列表、详情、预览、编辑、下载和删除。
- `/genre-map`：定位数据气泡图、表格、编辑、导入和导出。
- `/settings/modules`：既有题材模块和功能板块配置。
- `/genres/:slug`：既有参数化题材页面。

`/materials` 和 `/genre-map` 使用 Vue Router 懒加载。左侧固定导航至少包含：

- 素材库
- 题材定位图
- 题材配置

现有动态题材导航可以保留。素材和定位筛选必须同步到 URL 查询参数，页面刷新及浏览器前进、后退应恢复筛选状态。

## 前端页面与交互

### 素材库 `/materials`

页面包含：

1. 页面标题、素材总数和上传按钮。
2. 关键词、题材、素材类型、文件类型、标签、来源、上传时间和清空筛选。
3. 已选筛选条件、卡片/表格切换和排序。
4. 素材列表、分页和详情抽屉。
5. 查看、下载、编辑和删除操作。
6. 多文件拖拽上传、待上传列表、文件大小、移除操作、进度与逐文件结果。

基础预览：

- JPG、JPEG、PNG：图片预览。
- TXT、MD：读取并显示文本内容。
- PDF：浏览器内嵌或新标签打开。
- DOCX、XLSX、CSV：显示文件信息和下载按钮，不开发复杂 Office 在线预览。

### 题材定位图 `/genre-map`

页面顶部包含图表/表格切换、新增数据、导入数据、下载模板和导出数据。筛选项包含题材、平台、频道、周期、年龄层级、学历层级、趋势、是否重点和热度范围。

气泡图规则：

1. 横轴为 `average_age`。
2. 横轴分区：少年 12—22、中年 23—50、老年 51 以上。
3. 纵轴为学历层级：`low=1`、`medium=2`、`high=3`。
4. 气泡名称显示题材名称。
5. 气泡大小表示 `audience_share`。
6. 气泡颜色表示 `education_level`。
7. `is_core=true` 使用明显描边。
8. Tooltip 显示完整定位数据。
9. 图中显示年龄和学历分区背景。
10. 使用虚线显示当前筛选数据的平均年龄和平均学历位置。
11. 平均值优先按 `audience_share` 加权；没有有效占比时使用普通平均。
12. 每个九宫格区域显示当前区域用户占比合计。
13. 图例说明气泡大小和颜色含义。
14. 图表随容器宽度响应式调整。

点击气泡后打开详情抽屉，展示题材、年龄、学历、占比、热度、平台、周期和来源。“查看该题材素材”跳转至：

```text
/materials?genre_module_id={id}
```

表格展示题材、平台、频道、周期、年龄、学历、占比、热度、趋势、重点状态、样本量、数据来源、更新时间及操作。新增、修改或删除后，表格与气泡图均应立即刷新，重新加载页面后数据仍存在。

## 状态与视觉要求

- 延续 Sprint 2 的深黑蓝背景、深灰蓝卡片、橙色强调色和 8—12px 圆角，不推倒重做。
- 优先适配 1440px，并兼容 1280px 和 1024px。
- 必须处理 Loading、空状态、网络失败、表单校验和删除确认。
- 素材页面还须处理上传中、部分上传失败、预览失败和下载失败。
- 定位页面还须处理无图表数据、图表加载失败和导入失败明细。
- 不使用浏览器原生 `alert`。

## 测试要求

### 后端

保留现有测试，并至少覆盖：

1. 单文件与多文件上传成功。
2. 不允许的扩展名和超出大小限制失败。
3. 上传失败不残留文件。
4. 素材分页、题材、文件类型、时间和关键词筛选。
5. 素材元数据修改与文件下载。
6. 删除素材后清理物理文件。
7. 路径穿越文件名不能影响存储目录。
8. 定位数据新增、修改和删除。
9. 按平台、学历等条件筛选。
10. 年龄和用户占比范围校验。
11. Excel 与 CSV 导入。
12. 部分错误行返回明确明细。
13. 不存在题材时导入失败且不自动创建。
14. Excel 导出和 CSV 中文编码。

测试必须使用临时数据库和临时上传目录，不得污染开发数据库或正式 `storage`。

### 前端

保留现有测试，并至少覆盖：

1. 素材筛选参数发送及 URL 恢复。
2. 多文件上传列表、成功刷新和逐文件失败提示。
3. 文件类型筛选、素材编辑与删除确认。
4. 气泡坐标、大小与数据映射。
5. 点击气泡打开详情并携带题材参数跳转素材库。
6. 图表/表格切换。
7. 定位数据新增、修改和删除后刷新。
8. Excel 导入结果展示。

不得关闭 TypeScript 严格模式、删除测试换取通过，或使用大量 `any` 绕过类型检查。

## 验收标准

### 自动化验收

1. Sprint 1、Sprint 2 与 Sprint 3 后端测试全部通过。
2. `alembic check` 无未生成迁移差异。
3. 前端类型检查、全部单元测试和生产构建通过。
4. 测试不写入开发数据库和正式存储目录。

### 素材库手工验收

1. 打开 `/materials`，分别上传 PDF 和 DOCX，并批量上传 JPG、TXT、XLSX。
2. 为批次设置题材、素材类型、标签、来源和说明。
3. 刷新后素材和文件仍存在。
4. 题材、文件类型、关键词和时间筛选正确，筛选状态保留在 URL。
5. 修改素材标题后立即更新并持久化。
6. 下载文件使用原文件名且不暴露服务器路径。
7. 删除素材后列表记录和物理文件均被清理。
8. 部分上传失败时，成功文件保留，失败文件有逐项原因且无残留。

### 定位数据手工验收

1. 打开 `/genre-map` 新增一条定位数据，气泡立即出现。
2. 修改平均年龄后气泡横向移动。
3. 修改学历层级后气泡纵向移动。
4. 修改用户占比后气泡大小变化。
5. 图表和表格切换正常，表格可查看、编辑和删除。
6. 下载 Excel 模板并批量导入，逐行失败明细清晰。
7. 按平台、周期等筛选并导出当前结果，中文无乱码。
8. 点击气泡进入带对应题材参数的素材列表。
9. 筛选保留在 URL，刷新及浏览器前进、后退后可恢复。

### 运行与持久化验收

1. 重启前后端后，素材文件、元数据、定位数据和筛选能力正常。
2. 浏览器控制台无未处理错误。
3. 后端日志无未处理异常。
4. 1024px、1280px 和 1440px 下页面无关键内容遮挡或横向溢出。

## 完成定义

Sprint 3 只有在迁移、后端接口、文件安全、素材页面、定位页面、导入导出、自动化测试和手工验收全部完成后才算交付。最终报告应列出迁移与字段、文件变更、接口、路由、文件格式、存储位置、气泡映射、模板字段、测试与构建结果、启动命令和已知问题。

最终交付必须再次明确：没有实现登录、会员支付、权限系统、AI、自动采集、剧本项目、人物关系、复杂版本管理或多人协作。
