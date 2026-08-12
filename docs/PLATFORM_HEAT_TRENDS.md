# 上传平台与题材热度趋势

## 业务规则

- 素材库上传必须同时填写“上传平台”和“平台热度”；平台热度范围为 0—100。
- 剧本库不要求这两个字段，也不参与平台热度统计。
- 编辑素材时，平台与热度必须保持同时有值；允许同时清空历史记录的两项数据。
- 平台可以从常用平台中选择，也可以输入自定义名称。
- 平台名称使用 Unicode NFKC、去除首尾空格和忽略大小写的规则归并，展示名称采用最新有效记录的写法。

## 趋势图规则

访问 `/genre-map` 后，先选择上传平台。系统按素材的 UTC 上传月份聚合：

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
GET /api/genre-positioning/timeline?upload_platform=抖音
GET /api/materials?upload_platform=抖音
```

`GET /api/genre-positioning` 返回当前平台—题材汇总，可用于平台列表和总体信息；`timeline` 返回平台、完整月份序列、按题材和月份聚合的数据点及总素材数。

## 数据库迁移

迁移 `20260812_0008` 为 `materials` 增加：

- `upload_platform VARCHAR(100) NULL`
- `platform_heat FLOAT NULL`
- 平台查询索引与热度范围检查约束

旧素材保持两项为空，不会被迁移脚本猜测或改写。正式环境必须先完成可验证备份，再执行 `alembic upgrade head`。
