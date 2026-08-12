# 上传平台与题材热度趋势

## 业务规则

- 素材库上传必须同时填写“上传平台”和“平台热度”；平台热度范围为 0—100。
- 剧本库不要求这两个字段，也不参与平台热度统计。
- 编辑素材时，平台与热度必须保持同时有值；允许同时清空历史记录的两项数据。
- 平台可以从常用平台中选择，也可以输入自定义名称。
- 平台名称使用 Unicode NFKC、去除首尾空格和忽略大小写的规则归并，展示名称采用最新有效记录的写法。

## 趋势图规则

访问 `/genre-map` 后，平台选择框默认选中“全部平台”。“全部平台”把同一题材、同一月份在所有平台的有效素材直接合并求平均；也可改选一个具体平台。系统按素材的 UTC 上传月份聚合：

- 横轴：上传月份 `YYYY-MM`。
- 纵轴：该平台、该题材、该月素材的平台热度平均值，范围 0—100。
- 曲线：每个题材一条平滑曲线。
- 空档：某月没有有效素材时为 `null`，不补 0，也不连接断点。
- 提示：平台、题材、月份、平均热度、素材数量。
- 交互：点击数据点或表格“查看素材”，进入同时按题材与上传平台筛选的素材库。

只有未删除、`library_type=material`、题材启用且未删除、平台非空、热度有效的素材参与统计。自定义平台只要存在一条有效素材，就会自动出现在平台下拉框。

## API

```text
GET /api/genre-positioning
GET /api/genre-positioning?upload_platform=抖音
GET /api/genre-positioning/timeline
GET /api/genre-positioning/timeline?upload_platform=抖音
GET /api/materials?upload_platform=抖音
```

`GET /api/genre-positioning` 返回当前平台—题材汇总，可用于平台列表和总体信息；`timeline` 返回平台、完整月份序列、按题材和月份聚合的数据点及总素材数。

## 演示数据

项目提供独立演示工具，用真实数据库模型生成 36 条无附件虚拟素材，覆盖抖音、番茄小说、小红书和自定义平台“星河短剧”、最多 6 个题材及最近 6 个月。演示数据不会进入普通初始化 seed，标题统一以 `【趋势演示】` 开头，并携带双重专用标识。

运行前必须确认当前终端的 `DATABASE_URL` 指向允许写入的演示或便携数据库，不能误指正式数据库。生成命令：

```powershell
cd D:\文档存储\backend
.\.venv\Scripts\python.exe -m app.tools.seed_demo_heat
```

重复执行会更新同一批演示记录，不会产生重复数据。需要清理时运行：

```powershell
.\.venv\Scripts\python.exe -m app.tools.seed_demo_heat --remove
```

清理只永久删除同时具有 `platform-heat-demo-v1` 来源和完整 `platform_heat_demo` 元数据标记的记录，不处理真实素材、题材或附件。

## 数据库迁移

迁移 `20260812_0008` 为 `materials` 增加：

- `upload_platform VARCHAR(100) NULL`
- `platform_heat FLOAT NULL`
- 平台查询索引与热度范围检查约束

旧素材保持两项为空，不会被迁移脚本猜测或改写。正式环境必须先完成可验证备份，再执行 `alembic upgrade head`。
