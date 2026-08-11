# Sprint 2 · 动态题材与板块配置

## 实施范围

- 动态题材导航。
- 参数化题材页面 `/genres/:slug`。
- 模块设置页面 `/settings/modules`。
- 功能板块新增、编辑、启停、软删除和排序。
- `field_schema` 的结构保存与校验。
- 题材模块新增、编辑、启停、显示/隐藏、复制、软删除和排序。

## 明确不实施

- 素材 CRUD、素材卡片和动态素材表单。
- 题材气泡图和指标管理。
- 登录、支付、会员、AI 生成、网页采集。
- 任何前端 Mock 业务数据。

## 后端接口

### 题材模块

- `GET /api/genre-modules`
- `POST /api/genre-modules`
- `GET /api/genre-modules/{module_id}`
- `GET /api/genre-modules/slug/{slug}`
- `PATCH /api/genre-modules/{module_id}`
- `DELETE /api/genre-modules/{module_id}`
- `POST /api/genre-modules/{module_id}/duplicate`
- `POST /api/genre-modules/{module_id}/enable`
- `POST /api/genre-modules/{module_id}/disable`
- `PATCH /api/genre-modules/batch/reorder`

列表查询参数：`include_inactive`、`include_hidden`、`include_deleted`、`status`、`keyword`。

### 功能板块

- `GET /api/genre-modules/{module_id}/sections`
- `POST /api/genre-modules/{module_id}/sections`
- `GET /api/module-sections/{section_id}`
- `PATCH /api/module-sections/{section_id}`
- `DELETE /api/module-sections/{section_id}`
- `POST /api/module-sections/{section_id}/enable`
- `POST /api/module-sections/{section_id}/disable`
- `PATCH /api/module-sections/batch/reorder`

题材 slug 详情默认只返回启用板块；设置页面使用 `include_disabled=true` 获取全部未删除板块。

## 核心业务规则

- 普通导航只显示未删除、`status=active` 且 `visible=true` 的模块。
- 模块和板块排序必须由后端事务持久化。
- 复制模块时复制全部未删除板块，但不复制素材和指标；副本默认停用并隐藏。
- 模块 slug 全局唯一；同一模块内 `section_key` 唯一。
- 每个模块至少保留一个启用板块。
- `select` 和 `multiselect` 字段必须提供非空 `options`。
- 所有删除均为软删除。

## 前端路由

- `/`：进入模块设置或首个可用题材。
- `/genres/:slug`：题材独立页面。
- `/settings/modules`：模块与功能板块设置。

## 验收标准

1. 新增“规则怪谈”后导航即时出现并可进入 `/genres/rule-horror`。
2. 直接刷新参数化路由能够正常加载。
3. 新增“怪谈规则”板块后题材页面即时出现。
4. 调整排序并刷新后顺序保持。
5. 停用或隐藏模块后导航消失，设置页仍可见。
6. 再次启用或显示后导航恢复。
7. 复制模块时板块同步复制，副本默认停用和隐藏。
8. 重启后所有配置仍存在。
9. Sprint 1 与 Sprint 2 后端测试全部通过。
10. 前端类型检查、单元测试和生产构建全部通过。
