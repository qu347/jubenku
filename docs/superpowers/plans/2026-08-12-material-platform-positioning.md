# Material Platform Positioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Require upload platform and 0–100 platform heat for new material uploads, then let users select a platform and compare each genre's monthly heat curve in ECharts.

**Architecture:** Store platform metadata on each material and expose a new read-only `/api/genre-positioning` aggregation grouped by genre and normalized platform. The Vue page consumes only that aggregate endpoint; existing `genre_metrics` data and APIs remain untouched for database compatibility but disappear from the active UI.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy 2, Alembic, SQLite/PostgreSQL-compatible SQL, Pydantic 2, Vue 3, TypeScript, Pinia, Element Plus, ECharts 6, pytest, Vitest.

## Global Constraints

- `upload_platform` is required for new `library_type=material` uploads, trimmed, and at most 60 characters.
- `platform_heat` is required for new material uploads and must be between 0 and 100 inclusive.
- Script uploads do not require platform metadata and never contribute to positioning aggregates.
- Existing materials may retain null platform fields and remain readable; incomplete records do not contribute to aggregates.
- Aggregate results are computed live from active materials; do not write aggregate copies to `genre_metrics`.
- Keep the `genre_metrics` table and old API routes intact; do not expose their create/import/export UI on `/genre-map`.
- The active chart must use ECharts smooth multi-line series: selected platform, one line per genre, UTC upload months on the x-axis, a fixed 0–100 heat axis, horizontal `dataZoom`, end labels, and `richText` tooltip rendering.
- Do not add background jobs, threads, queues, web scraping, authentication, payments, or AI generation.
- Every production change follows RED → GREEN → REFACTOR, and no task may modify the original retained database directly.

---

### Task 1: Persist and validate material platform metadata

**Files:**
- Create: `backend/alembic/versions/20260812_0008_material_platform_positioning.py`
- Modify: `backend/app/models/material.py`
- Modify: `backend/app/schemas/material.py`
- Modify: `backend/app/api/endpoints/materials.py`
- Modify: `backend/app/services/material_service.py`
- Test: `backend/tests/test_material_positioning.py`
- Test: `backend/tests/test_sprint3_migration.py`

**Interfaces:**
- Produces model fields `Material.upload_platform: str | None` and `Material.platform_heat: float | None`.
- Extends `MaterialRead`, `MaterialUpdate`, upload multipart data, and `material_to_dict()` with the same property names.
- Produces `validate_platform_metadata(library_type, upload_platform, platform_heat)` behavior used by upload and update paths.

- [ ] **Step 1: Write failing upload and serialization tests**

Add tests that call the real upload endpoint and assert required fields, boundary values, script exemption, and response serialization:

```python
def test_material_upload_requires_platform_metadata(client, genre_module, markdown_upload):
    response = client.post(
        "/api/materials/upload",
        data={"library_type": "material", "genre_module_id": genre_module["id"]},
        files={"files": markdown_upload},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "material_platform_required"


@pytest.mark.parametrize("heat", [0, 100])
def test_material_upload_accepts_heat_boundaries(client, genre_module, markdown_upload, heat):
    response = client.post(
        "/api/materials/upload",
        data={
            "library_type": "material",
            "genre_module_id": genre_module["id"],
            "upload_platform": "  番茄小说  ",
            "platform_heat": str(heat),
        },
        files={"files": markdown_upload},
    )
    assert response.status_code == 200
    item = response.json()["data"]["materials"][0]
    assert item["upload_platform"] == "番茄小说"
    assert item["platform_heat"] == heat


def test_script_upload_does_not_require_platform_metadata(client, genre_module, markdown_upload):
    response = client.post(
        "/api/materials/upload",
        data={"library_type": "script", "genre_module_id": genre_module["id"]},
        files={"files": markdown_upload},
    )
    assert response.status_code == 200
    assert response.json()["data"]["materials"][0]["upload_platform"] is None
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_positioning.py -q
```

Expected: failures because upload fields and response properties do not exist and missing metadata is still accepted.

- [ ] **Step 3: Add the nullable columns and migration**

Add model fields:

```python
upload_platform: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
platform_heat: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
```

Create revision `20260812_0008` with `down_revision = "20260812_0007"`. Use `batch_alter_table("materials")` to add both nullable columns, `ix_materials_upload_platform`, `ix_materials_platform_heat`, and a named check constraint `ck_materials_platform_heat_range` equivalent to `platform_heat IS NULL OR (platform_heat >= 0 AND platform_heat <= 100)`. Downgrade removes the constraint, indexes, and columns in reverse order. Do not update existing rows.

- [ ] **Step 4: Implement request and service validation**

Extend the multipart endpoint with:

```python
upload_platform: Annotated[str | None, Form(max_length=60)] = None
platform_heat: Annotated[float | None, Form(ge=0, le=100)] = None
```

Normalize and validate the final pair in the service:

```python
def validate_platform_metadata(
    library_type: str,
    upload_platform: str | None,
    platform_heat: float | None,
    *,
    require_for_material: bool,
) -> tuple[str | None, float | None]:
    platform = upload_platform.strip() if upload_platform else None
    if platform_heat is not None and not 0 <= platform_heat <= 100:
        raise AppException(
            "平台热度必须在 0 到 100 之间",
            status_code=422,
            code="invalid_platform_heat",
        )
    if library_type == "material" and require_for_material and (not platform or platform_heat is None):
        raise AppException(
            "请选择或输入上传平台，并填写平台热度",
            status_code=422,
            code="material_platform_required",
        )
    if bool(platform) != (platform_heat is not None):
        raise AppException(
            "上传平台和平台热度必须同时填写或同时清空",
            status_code=422,
            code="incomplete_platform_metadata",
        )
    return platform, platform_heat
```

Upload calls it with `require_for_material=True`. Update resolves omitted fields against the current record, validates the resulting pair with `require_for_material=False`, and permits legacy material records to remain empty. Include both properties in `MaterialRead`, `MaterialUpdate`, and `material_to_dict()`.

- [ ] **Step 5: Add migration round-trip coverage**

Extend the temporary-database migration test to assert revision 0008 adds nullable columns, preserves all legacy rows with null values, passes `alembic check`, downgrades to 0007, and upgrades again without changing legacy material counts or text fields.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_positioning.py tests/test_sprint3_migration.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 1**

```powershell
git add backend/app/models/material.py backend/app/schemas/material.py backend/app/api/endpoints/materials.py backend/app/services/material_service.py backend/alembic/versions/20260812_0008_material_platform_positioning.py backend/tests/test_material_positioning.py backend/tests/test_sprint3_migration.py
git commit -m "feat: add material platform metadata"
```

---

### Task 2: Add live genre-platform aggregation API

**Files:**
- Create: `backend/app/schemas/genre_positioning.py`
- Create: `backend/app/repositories/genre_positioning_repository.py`
- Create: `backend/app/services/genre_positioning_service.py`
- Create: `backend/app/api/endpoints/genre_positioning.py`
- Modify: `backend/app/api/endpoints/__init__.py`
- Modify: `backend/app/api/router.py`
- Modify: `backend/app/repositories/material_repository.py`
- Modify: `backend/app/services/material_service.py`
- Modify: `backend/app/api/endpoints/materials.py`
- Test: `backend/tests/test_material_positioning.py`

**Interfaces:**
- Produces `GET /api/genre-positioning` returning `ApiResponse[GenrePositioningList]`.
- Produces response item fields `genre_module_id`, `genre_name`, `theme_color`, `upload_platform`, `average_heat`, `material_count`, `latest_updated_at`.
- Extends `GET /api/materials` with exact case-insensitive `upload_platform` filtering.

- [ ] **Step 1: Write failing aggregate and filter tests**

Create real materials in the temporary test database and assert grouping behavior:

```python
def test_positioning_groups_materials_by_genre_and_platform(client, create_material):
    genre = create_material(platform="番茄小说", heat=80).genre_module
    create_material(genre=genre, platform="番茄小说", heat=90)
    create_material(genre=genre, platform="  番茄小说  ", heat=85)

    response = client.get("/api/genre-positioning")
    assert response.status_code == 200
    assert response.json()["data"]["items"] == [{
        "genre_module_id": genre.id,
        "genre_name": genre.name,
        "theme_color": genre.theme_color,
        "upload_platform": "番茄小说",
        "average_heat": 85.0,
        "material_count": 3,
        "latest_updated_at": response.json()["data"]["items"][0]["latest_updated_at"],
    }]
```

Add separate tests proving scripts, deleted materials, incomplete legacy materials, and deleted genres are excluded; different genre/platform pairs remain separate; heat filters apply after averaging; material listing accepts `upload_platform`; PATCH and DELETE immediately change the next aggregate response.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_positioning.py -q
```

Expected: 404 for `/api/genre-positioning` and material platform filtering returns unfiltered rows.

- [ ] **Step 3: Define aggregate schemas and repository query**

Define:

```python
class GenrePositioningItem(BaseModel):
    genre_module_id: str
    genre_name: str
    theme_color: str
    upload_platform: str
    average_heat: float
    material_count: int
    latest_updated_at: datetime


class GenrePositioningList(BaseModel):
    items: list[GenrePositioningItem]
    total: int
```

Repository `list(...) -> list[dict[str, Any]]` must join active `GenreModule`, filter active material-library rows with complete platform metadata, group by `Material.genre_module_id` and `func.lower(func.trim(Material.upload_platform))`, calculate `avg`, `count`, and `max(updated_at)`, apply aggregate heat bounds using `HAVING`, and sort by average heat descending then genre/platform ascending. Build a second subquery using `row_number().over(partition_by=(genre_module_id, normalized_platform), order_by=(updated_at.desc(), id.desc()))`; join its `row_number == 1` row to the aggregate so `upload_platform` always uses the most recently updated spelling on both SQLite and PostgreSQL.

- [ ] **Step 4: Add service, endpoint, router, and material filter**

Endpoint parameters:

```python
genre_module_id: UUID | None = None
upload_platform: str | None = Query(default=None, max_length=60)
heat_min: float | None = Query(default=None, ge=0, le=100)
heat_max: float | None = Query(default=None, ge=0, le=100)
```

Service rejects `heat_min > heat_max` with code `invalid_heat_range`, rounds `average_heat` to one decimal, and returns `{"items": items, "total": len(items)}`. Register the new router. Extend material repository/service/endpoint list signatures with `upload_platform` and exact case-insensitive trimmed matching.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_positioning.py -q
```

Expected: all aggregate, filter, update, and delete cases pass.

- [ ] **Step 6: Commit Task 2**

```powershell
git add backend/app/schemas/genre_positioning.py backend/app/repositories/genre_positioning_repository.py backend/app/services/genre_positioning_service.py backend/app/api/endpoints/genre_positioning.py backend/app/api/endpoints/__init__.py backend/app/api/router.py backend/app/repositories/material_repository.py backend/app/services/material_service.py backend/app/api/endpoints/materials.py backend/tests/test_material_positioning.py
git commit -m "feat: aggregate genre platform positioning"
```

---

### Task 3: Add platform metadata to the material workflow

**Files:**
- Modify: `frontend/src/config/materials.ts`
- Modify: `frontend/src/types/material.ts`
- Modify: `frontend/src/api/materials.ts`
- Modify: `frontend/src/components/material/MaterialUploadDrawer.vue`
- Modify: `frontend/src/components/material/MaterialDetailDrawer.vue`
- Modify: `frontend/src/components/material/MaterialFilterBar.vue`
- Modify: `frontend/src/components/material/MaterialTable.vue`
- Modify: `frontend/src/components/material/MaterialCardGrid.vue`
- Modify: `frontend/src/views/materials/MaterialLibraryView.vue`
- Test: `frontend/src/__tests__/sprint3.materials.spec.ts`
- Test: `frontend/src/__tests__/materialPlatform.spec.ts`

**Interfaces:**
- Produces `COMMON_UPLOAD_PLATFORMS: readonly string[]`.
- Extends `Material`, `MaterialUploadPayload`, `MaterialUpdatePayload`, and `MaterialFilters` with `upload_platform` and `platform_heat`.
- Upload API appends both multipart fields only when present.

- [ ] **Step 1: Write failing component and API tests**

Mount the real upload drawer and assert material mode requires both inputs while script mode does not. Assert `allow-create` custom platform behavior and FormData serialization:

```typescript
it('requires platform and heat for material uploads', async () => {
  const wrapper = mount(MaterialUploadDrawer, materialDrawerOptions)
  await wrapper.get('[data-test="submit-upload"]').trigger('click')
  expect(wrapper.text()).toContain('请选择或输入上传平台')
  expect(wrapper.text()).toContain('请填写 0 到 100 的平台热度')
})

it('serializes custom platform and heat', async () => {
  await uploadMaterials({ ...payload, upload_platform: '自定义平台', platform_heat: 88 })
  expect(postedFormData.get('upload_platform')).toBe('自定义平台')
  expect(postedFormData.get('platform_heat')).toBe('88')
})
```

Add tests for detail/edit display, legacy “平台信息待补充”, table/card rendering, and `upload_platform` route/filter synchronization.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
cd frontend
pnpm run test:unit -- src/__tests__/materialPlatform.spec.ts src/__tests__/sprint3.materials.spec.ts
```

Expected: missing controls/properties and FormData assertions fail.

- [ ] **Step 3: Implement types, options, and API serialization**

Add:

```typescript
export const COMMON_UPLOAD_PLATFORMS = [
  '番茄小说', '七猫', '起点中文网', '晋江文学城', '纵横中文网',
  '抖音', '快手', '小红书', '微信公众号', '知乎',
] as const
```

Add `upload_platform: string | null` and `platform_heat: number | null` to read types and nullable optional properties to update/filter types. Define upload payload as a discriminated union: the material branch requires `upload_platform: string` and `platform_heat: number`, while the script branch declares both properties optional and undefined. Append values to FormData only when present.

- [ ] **Step 4: Implement upload, edit, detail, list, and filter UI**

Use Element Plus `el-select` with `filterable`, `allow-create`, and `default-first-option` for platform. Use `el-input-number` with `min=0`, `max=100`, and `step=1` for heat. Show controls only when `library_type === 'material'`; reset them when switching to script mode. Validate before emitting upload.

Display platform and heat in material detail/edit and compactly in table/cards. Legacy rows display “平台信息待补充”. Add platform selection/custom entry to `MaterialFilterBar`, preserve it in route query serialization, and do not show it in script library mode.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```powershell
cd frontend
pnpm run test:unit -- src/__tests__/materialPlatform.spec.ts src/__tests__/sprint3.materials.spec.ts
pnpm run type-check
```

Expected: focused tests and TypeScript checking pass.

- [ ] **Step 6: Commit Task 3**

```powershell
git add frontend/src/config/materials.ts frontend/src/types/material.ts frontend/src/api/materials.ts frontend/src/components/material/MaterialUploadDrawer.vue frontend/src/components/material/MaterialDetailDrawer.vue frontend/src/components/material/MaterialFilterBar.vue frontend/src/components/material/MaterialTable.vue frontend/src/components/material/MaterialCardGrid.vue frontend/src/views/materials/MaterialLibraryView.vue frontend/src/__tests__/sprint3.materials.spec.ts frontend/src/__tests__/materialPlatform.spec.ts
git commit -m "feat: collect material platform heat"
```

---

### Task 4: Add selected-platform monthly genre timeline API

**Files:**
- Modify: `backend/app/schemas/genre_positioning.py`
- Modify: `backend/app/repositories/genre_positioning_repository.py`
- Modify: `backend/app/services/genre_positioning_service.py`
- Modify: `backend/app/api/endpoints/genre_positioning.py`
- Test: `backend/tests/test_material_positioning.py`

**Interfaces:**
- Produces `GET /api/genre-positioning/timeline?upload_platform=<platform>`.
- Produces `GenrePositioningTimeline` with `upload_platform`, `periods`, `points`, and `total_materials`.
- Each point contains `genre_module_id`, `genre_name`, `theme_color`, `period`, `average_heat`, and `material_count`.

- [ ] **Step 1: Write failing monthly aggregation tests**

Create active materials with explicit UTC `created_at` values across months, genres, and platforms. Assert exact platform matching, monthly grouping, average heat, counts, ascending `YYYY-MM` periods, inactive/deleted/incomplete/script exclusions, and no synthetic point for a missing month:

```python
def test_timeline_groups_selected_platform_by_genre_and_upload_month(client, create_material):
    fantasy = create_material(platform="抖音", heat=80, created_at="2026-06-03T00:00:00Z")
    create_material(genre=fantasy.genre_module, platform="抖音", heat=100, created_at="2026-06-20T00:00:00Z")
    create_material(genre=fantasy.genre_module, platform="抖音", heat=70, created_at="2026-08-01T00:00:00Z")

    response = client.get("/api/genre-positioning/timeline", params={"upload_platform": " 抖音 "})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["periods"] == ["2026-06", "2026-08"]
    assert [(p["period"], p["average_heat"], p["material_count"]) for p in data["points"]] == [
        ("2026-06", 90.0, 2),
        ("2026-08", 70.0, 1),
    ]
```

Also assert omitted/blank platform returns 422 and custom platforms appear in existing `/api/genre-positioning` results used by the dropdown.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_positioning.py -q --basetemp ../.runtime/pytest-timeline-red
```

Expected: timeline route returns 404.

- [ ] **Step 3: Implement schemas and portable repository query**

Define:

```python
class GenrePositioningTimelinePoint(BaseModel):
    genre_module_id: str
    genre_name: str
    theme_color: str
    period: str
    average_heat: float
    material_count: int


class GenrePositioningTimeline(BaseModel):
    upload_platform: str
    periods: list[str]
    points: list[GenrePositioningTimelinePoint]
    total_materials: int
```

Repository `timeline(upload_platform: str) -> list[Material]` selects only valid material rows for an active genre and exact `lower(trim(upload_platform))` match. Use Python to group by `created_at.astimezone(timezone.utc).strftime("%Y-%m")` and genre so behavior is identical on SQLite and PostgreSQL; calculate rounded means and counts in the service. Return only observed months.

- [ ] **Step 4: Add endpoint and response ordering**

Register `/timeline` before `/{metric_id}`-style dynamic paths are relevant. Normalize the required query platform, reject blank input with code `platform_required`, order `periods` ascending, and order points by period then genre name and ID. Use the most recently updated matching material's trimmed platform spelling in `upload_platform`.

- [ ] **Step 5: Run focused and full backend tests**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_positioning.py -q --basetemp ../.runtime/pytest-timeline-green
.\.venv\Scripts\python.exe -m pytest -q --basetemp ../.runtime/pytest-timeline-all
```

Expected: all focused and all backend tests pass.

- [ ] **Step 6: Commit Task 4**

```powershell
git add backend/app/schemas/genre_positioning.py backend/app/repositories/genre_positioning_repository.py backend/app/services/genre_positioning_service.py backend/app/api/endpoints/genre_positioning.py backend/tests/test_material_positioning.py
git commit -m "feat: add platform genre heat timeline"
```

---

### Task 5: Replace the audience map with an ECharts platform genre trend chart

**Files:**
- Create: `frontend/src/types/genrePositioning.ts`
- Create: `frontend/src/api/genrePositioning.ts`
- Create: `frontend/src/stores/genrePositioning.ts`
- Create: `frontend/src/components/genre-map/GenreHeatTrendChart.vue`
- Create: `frontend/src/components/genre-map/GenrePositioningTable.vue`
- Modify: `frontend/src/views/GenreMapView.vue`
- Modify: `frontend/src/components/module/AppLayout.vue`
- Test: `frontend/src/__tests__/genrePositioning.spec.ts`
- Test: `frontend/src/__tests__/sprint3.navigation.spec.ts`

**Interfaces:**
- Produces TypeScript types matching Task 4 timeline and Task 2 current aggregate responses.
- Produces `listGenrePositioning()` for platform options and `getGenrePositioningTimeline(uploadPlatform)` for chart/table data.
- Store exposes `platforms`, `selectedPlatform`, `timeline`, `loading`, `error`, `fetchPlatforms`, `selectPlatform`.
- Chart emits `select: [point: GenrePositioningTimelinePoint]`.

- [ ] **Step 1: Write failing page, API/store, chart option, and navigation tests**

Test the approved interaction:

```typescript
it('selects one platform and draws one line per genre over upload months', async () => {
  const wrapper = mountGenreMap(timelineFixture)
  expect(wrapper.text()).toContain('题材平台热度趋势图')
  expect(wrapper.text()).toContain('选择平台')
  expect(wrapper.text()).not.toContain('平均年龄')
  expect(wrapper.text()).not.toContain('新增数据')
  expect(chartOption.series.map((series) => series.name)).toEqual(['西方奇幻', '悬疑灵异'])
})

it('opens the selected platform and point genre in the material library', async () => {
  chartEmit('select', timelineFixture.points[0])
  expect(router.currentRoute.value.query).toMatchObject({
    genre_module_id: 'genre-1',
    upload_platform: '抖音',
  })
})
```

Assert platform options are derived from all current aggregate items and deduplicated case-insensitively, including a custom platform. Assert selecting a platform calls timeline with that exact selection.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
cd frontend
node D:\文档存储\frontend\node_modules\vitest\vitest.mjs run src/__tests__/genrePositioning.spec.ts src/__tests__/sprint3.navigation.spec.ts
```

Expected: old age/education UI remains and timeline modules do not exist.

- [ ] **Step 3: Implement types, API, and store**

Use the Task 4 response types. `fetchPlatforms()` calls `/genre-positioning`, derives unique trimmed platform names, sorts them with Chinese locale comparison, preserves a still-valid selection, otherwise selects the first platform, then loads its timeline. Empty platform results clear the timeline and show an upload guidance state. `selectPlatform()` loads only the chosen platform and ignores stale out-of-order responses with a monotonically increasing request token.

- [ ] **Step 4: Implement ECharts smooth multi-line option**

Each genre becomes one `line` series with `smooth: true`, circle symbols, theme color, `connectNulls: false`, and `endLabel.formatter: '{a}'`. Build each series data array against the complete sorted `periods` list, using `null` for missing points. The y-axis is value `min: 0`, `max: 100`; the x-axis is category months. Add horizontal inside/slider `dataZoom` when more than 12 months. Tooltip must use `renderMode: 'richText'` and newline-separated plain text with selected platform, genre, month, average heat, and material count. Export a pure `buildGenreHeatTrendOption()` for deterministic tests.

- [ ] **Step 5: Replace the active page and table**

Remove old metric CRUD/import/export/editor/detail components from `GenreMapView.vue`. Place a searchable platform `el-select` beside the chart/table switch. The table columns are topic, platform, upload month, average heat, material count, and view material. Summaries show selected platform, unique genre count, observed month count, and material-weighted platform heat. Preserve local chart/table view preference and route `/genre-map`; navigation label becomes “平台热度趋势”. Clicking a point or table action navigates with topic and platform query filters.

- [ ] **Step 6: Run focused tests and type checking**

Run separately:

```powershell
cd frontend
node D:\文档存储\frontend\node_modules\vitest\vitest.mjs run src/__tests__/genrePositioning.spec.ts src/__tests__/sprint3.navigation.spec.ts
node D:\文档存储\frontend\node_modules\vue-tsc\bin\vue-tsc.js -b
```

Expected: focused tests and type checking pass without watch mode.

- [ ] **Step 7: Commit Task 5**

```powershell
git add frontend/src/types/genrePositioning.ts frontend/src/api/genrePositioning.ts frontend/src/stores/genrePositioning.ts frontend/src/components/genre-map/GenreHeatTrendChart.vue frontend/src/components/genre-map/GenrePositioningTable.vue frontend/src/views/GenreMapView.vue frontend/src/components/module/AppLayout.vue frontend/src/__tests__/genrePositioning.spec.ts frontend/src/__tests__/sprint3.navigation.spec.ts
git commit -m "feat: show platform genre heat trends"
```

---

### Task 6: Documentation, regression, migration, and runtime acceptance

**Files:**
- Modify: `README.md`
- Modify: `docs/PRODUCT_SPEC.md`
- Modify: `docs/USER_GUIDE.md`
- Modify: `docs/SPRINT_3.md`
- Modify: `docs/SPRINT_4.md`
- Modify: `docs/RELEASE_CHECKLIST.md`
- Modify: `docs/BACKUP_RESTORE.md`
- Test: `backend/tests/test_material_positioning.py`
- Test: `frontend/src/__tests__/genrePositioning.spec.ts`

**Interfaces:**
- Documents the final upload fields, current and monthly aggregation rules, old-data behavior, and both `/api/genre-positioning` endpoints.
- Produces a rebuilt `frontend/dist` consumed by production static hosting.

- [ ] **Step 1: Update product and user documentation**

Replace active age/education positioning instructions with the approved platform-selected monthly genre curve workflow. Explicitly state that old `genre_metrics` data is retained but not used by the page, historical materials must be supplemented before appearing, scripts never enter positioning aggregation, months come from UTC upload time, and missing months remain gaps. Update release and restore checks accordingly.

- [ ] **Step 2: Run the full backend suite sequentially**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all tests pass. Do not run this simultaneously with the full frontend suite because the existing SQLite concurrency test is sensitive to artificial CPU/disk contention.

- [ ] **Step 3: Verify Alembic on a temporary database copy**

Create an ignored database copy under `.runtime`, point `DATABASE_URL` to that copy only, then run:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe check
```

Expected: head is `20260812_0008`, check reports no new upgrade operations, legacy materials remain present, and new fields are null on legacy rows. Never use `backend/script_materials.db` or the formal production database for this verification.

- [ ] **Step 4: Run full frontend verification and build**

Run sequentially:

```powershell
cd frontend
pnpm run type-check
pnpm run test:unit
pnpm run build
```

Expected: TypeScript, all Vitest files, and production build pass. Existing dependency chunk-size notices are acceptable; test or compiler errors are not.

- [ ] **Step 5: Perform safe runtime acceptance**

Restart the existing single-worker service only after confirming the listener PID. Apply migration 0008 to the configured non-production/development runtime database, open `/materials` and `/genre-map`, then verify:

1. material upload cannot submit without platform and heat;
2. a custom platform with heat 85 uploads successfully;
3. the custom platform appears in the dropdown and can be selected;
4. the ECharts line chart shows one genre curve with the correct month, heat, and count;
5. clicking the curve point opens the filtered material list;
6. editing heat changes the monthly point;
7. deleting the temporary material removes its point when it was the last member;
8. no QA material or upload file remains after acceptance.

- [ ] **Step 6: Commit Task 6**

```powershell
git add README.md docs/PRODUCT_SPEC.md docs/USER_GUIDE.md docs/SPRINT_3.md docs/SPRINT_4.md docs/RELEASE_CHECKLIST.md docs/BACKUP_RESTORE.md frontend/dist
git commit -m "docs: finalize platform positioning workflow"
```

- [ ] **Step 7: Final integrity review**

Run:

```powershell
git diff --check
git status --short
```

Confirm all intended source, migration, tests, docs, and dist files are accounted for; unrelated pre-existing working-tree changes remain preserved; the active database and storage contain no temporary acceptance records.
