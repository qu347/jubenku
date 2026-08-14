# Material Uploader Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fixed three-person uploader filter to the material library and insert six real example materials into the current portable database.

**Architecture:** Extend the existing `MaterialFilters` request path end-to-end: Vue filter component and URL query, FastAPI query validation, Service forwarding, and SQLAlchemy repository filtering. Keep the uploader list as a frontend constant because the approved scope permits exactly three names. Populate examples through the existing upload API so database rows and Markdown attachments follow production validation and storage rules.

**Tech Stack:** Vue 3, TypeScript, Pinia, Vue Router, Element Plus, FastAPI, SQLAlchemy, SQLite, Vitest, Pytest.

## Global Constraints

- Show the uploader filter only in the material library, never in the script library.
- The only selectable names are `董凤`, `张靖宇`, and `陈仁杰`.
- Match the trimmed uploader name exactly; do not implement fuzzy search or personnel management.
- Combine uploader with all other material filters using AND semantics.
- Preserve the uploader in the URL and restore it after refresh.
- Insert exactly six identifiable example materials into the current `.runtime/portable` database, two per uploader.
- Example titles start with `[上传人筛选测试]` and use real Markdown attachments.
- Do not overwrite or recreate the current database.

---

### Task 1: Backend uploader query

**Files:**
- Modify: `backend/tests/test_material_positioning.py`
- Modify: `backend/app/api/endpoints/materials.py`
- Modify: `backend/app/services/material_service.py`
- Modify: `backend/app/repositories/material_repository.py`

**Interfaces:**
- Consumes: existing `Material.uploaded_by: str` model field.
- Produces: `GET /api/materials?uploaded_by=<name>` with trimmed exact matching.
- Produces: `MaterialService.list(..., uploaded_by: str | None, ...)` and `MaterialRepository.list(..., uploaded_by: str | None, ...)`.

- [ ] **Step 1: Write failing API tests**

Add tests that create materials for all three people, request `uploaded_by=董凤`, and assert only Dong Feng's records are returned. Add a second test combining `uploaded_by` and `upload_platform` to prove AND semantics. Use surrounding whitespace in the stored value and request to prove trimming.

```python
def test_material_list_filters_uploaded_by_exactly(client, create_material):
    matching = create_material(uploaded_by="  董凤  ")
    create_material(genre=matching.genre_module, uploaded_by="张靖宇")

    response = client.get("/api/materials", params={"uploaded_by": " 董凤 "})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["data"]["items"]] == [matching.id]
```

- [ ] **Step 2: Run the focused backend tests and verify RED**

Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_material_positioning.py -k uploaded_by -q
```

Expected: the response still contains nonmatching uploaders because `uploaded_by` is not accepted or forwarded.

- [ ] **Step 3: Add the endpoint and service parameter**

Add to `list_materials`:

```python
uploaded_by: str | None = Query(default=None, max_length=100),
```

Forward it unchanged through `MaterialService.list` and into `MaterialRepository.list`.

- [ ] **Step 4: Add repository exact matching**

Add the predicate only when the trimmed request is nonempty:

```python
if uploaded_by and uploaded_by.strip():
    statement = statement.where(
        func.trim(Material.uploaded_by) == uploaded_by.strip()
    )
```

This remains a separate SQLAlchemy `WHERE` clause, preserving AND semantics with platform, genre, tags, dates, and other filters.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run the command from Step 2. Expected: all uploader tests pass.

- [ ] **Step 6: Commit backend filter**

```powershell
git add backend/tests/test_material_positioning.py backend/app/api/endpoints/materials.py backend/app/services/material_service.py backend/app/repositories/material_repository.py
git commit -m "feat: filter materials by uploader"
```

### Task 2: Frontend fixed uploader selector and URL state

**Files:**
- Modify: `frontend/src/types/material.ts`
- Modify: `frontend/src/components/material/MaterialFilterBar.vue`
- Modify: `frontend/src/views/materials/MaterialLibraryView.vue`
- Modify: `frontend/src/__tests__/materialPlatform.spec.ts`

**Interfaces:**
- Consumes: backend `uploaded_by` query parameter from Task 1.
- Produces: `MaterialFilters.uploaded_by?: string`.
- Produces: exported or component-local fixed names `['董凤', '张靖宇', '陈仁杰']`.

- [ ] **Step 1: Write failing component and route tests**

Extend the existing material platform filter test suite to assert:

```typescript
expect(materialFilter.find('[data-test="filter-uploader"]').exists()).toBe(true)
expect(materialFilter.text()).toContain('董凤')
expect(materialFilter.text()).toContain('张靖宇')
expect(materialFilter.text()).toContain('陈仁杰')
expect(scriptFilter.find('[data-test="filter-uploader"]').exists()).toBe(false)
```

Mount `/materials?uploaded_by=董凤`, wait for the initial fetch, and assert the HTTP request params contain `uploaded_by: '董凤'`. Emit an apply event with another uploader and assert the route query changes.

- [ ] **Step 2: Run the focused frontend test and verify RED**

Run:

```powershell
cd frontend
pnpm exec vitest run src/__tests__/materialPlatform.spec.ts
```

Expected: the uploader selector does not exist and the route does not forward `uploaded_by`.

- [ ] **Step 3: Extend the filter type and component state**

Add `uploaded_by?: string` to `MaterialFilters`, add it to `emptyFilters`, and define only the approved values:

```typescript
const uploaders = ['董凤', '张靖宇', '陈仁杰'] as const
```

Render the selector after upload platform only for `libraryType === 'material'`:

```vue
<el-select v-if="libraryType === 'material'" v-model="draft.uploaded_by" data-test="filter-uploader" clearable placeholder="上传人">
  <el-option v-for="name in uploaders" :key="name" :label="name" :value="name" />
</el-select>
```

In `submit`, clear `uploaded_by` for the script library.

- [ ] **Step 4: Add URL parsing and chip label**

In `filtersFromQuery`, read `uploaded_by` only when `libraryType === 'material'`. Add `uploaded_by: '上传人'` to `chipLabel`. The generic `toQuery` and `removeChip` paths then preserve and clear it without special handling.

- [ ] **Step 5: Run focused test and type check**

```powershell
cd frontend
pnpm exec vitest run src/__tests__/materialPlatform.spec.ts
pnpm run type-check
```

Expected: tests and type check pass.

- [ ] **Step 6: Commit frontend filter**

```powershell
git add frontend/src/types/material.ts frontend/src/components/material/MaterialFilterBar.vue frontend/src/views/materials/MaterialLibraryView.vue frontend/src/__tests__/materialPlatform.spec.ts
git commit -m "feat: add fixed uploader filter"
```

### Task 3: Insert six real current-database examples

**Files:**
- Runtime data only: `.runtime/portable/database/script_materials.db`
- Runtime attachments only: `.runtime/portable/storage/materials/<year>/<month>/*.md`

**Interfaces:**
- Consumes: existing `POST /api/materials/upload` multipart endpoint.
- Produces: six `library_type=material` records and six valid Markdown attachments.

- [ ] **Step 1: Check for existing example titles**

Query the current API for keyword `[上传人筛选测试]`. Stop if six matching examples already exist; do not duplicate them.

- [ ] **Step 2: Prepare six UTF-8 Markdown fixtures in a workspace temporary directory**

Use two distinct titles per person, such as:

```text
[上传人筛选测试] 董凤-都市反转开场
[上传人筛选测试] 董凤-悬疑线索设计
[上传人筛选测试] 张靖宇-仙侠人物冲突
[上传人筛选测试] 张靖宇-末世场景样例
[上传人筛选测试] 陈仁杰-都市情感转折
[上传人筛选测试] 陈仁杰-历史权谋对白
```

Each file includes a short synopsis and test purpose, not empty placeholder text.

- [ ] **Step 3: Upload through the real API**

For each fixture, call `POST /api/materials/upload` with:

```text
library_type=material
genre_module_id=<an existing active module>
material_type=剧情
title=<the fixture title>
uploaded_by=<one approved uploader>
project_owner=筛选测试负责人
upload_platform=抖音
platform_heat=<distinct value from 55 to 90>
source=上传人筛选功能测试
description=<fixture synopsis>
tags=[]
```

Require a successful response and retain every returned material ID for verification.

- [ ] **Step 4: Verify current database and API results**

Query each uploader and assert exactly two titles with the test prefix are present. Query `uploaded_by=董凤&upload_platform=抖音` and confirm the two Dong Feng examples are returned. Run `PRAGMA integrity_check` read-only and require `ok`.

### Task 4: Final regression, build, and running application refresh

**Files:**
- Generated: `frontend/dist/**`

**Interfaces:**
- Consumes: completed backend, frontend, and current data tasks.
- Produces: a fresh production frontend bundle and a running application serving the new uploader filter.

- [ ] **Step 1: Run backend focused and full tests**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_material_positioning.py -k "uploaded_by or upload_platform" -q
.\.venv\Scripts\python.exe -m pytest -q
```

- [ ] **Step 2: Run frontend focused tests and type check**

```powershell
cd frontend
pnpm exec vitest run src/__tests__/materialPlatform.spec.ts
pnpm run type-check
```

- [ ] **Step 3: Build production frontend**

```powershell
cd frontend
pnpm run build
```

- [ ] **Step 4: Refresh the local service safely**

Confirm the existing listener belongs to this project before stopping it, restart the single-worker FastAPI service, and verify `/api/health/ready` reports `ready`. Do not stop unrelated Python processes.

- [ ] **Step 5: Verify the delivered behavior**

Confirm the material library request contains `uploaded_by`, each fixed name returns its two example records, the script library sends no uploader filter, and the refreshed page uses the newly generated `frontend/dist` asset.

- [ ] **Step 6: Commit generated delivery changes if tracked**

Commit only task-related tracked files; preserve unrelated working-tree changes.
