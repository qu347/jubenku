# Persistent Upload Platforms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Save every custom upload platform in SQLite so all users and all platform selectors can reuse it after refresh or on another computer.

**Architecture:** Add an independent `upload_platforms` catalog without changing the historical string stored on each material. A FastAPI repository/service/API exposes catalog list and create operations; a shared Pinia store merges the server catalog with built-in fallback values and feeds upload, edit, filtering, and positioning controls.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy, Alembic, SQLite/PostgreSQL-compatible models, Vue 3, TypeScript, Pinia, Element Plus, Vitest, pytest.

## Global Constraints

- UUID primary keys, UTC timestamps, soft deletion, typed SQLAlchemy models, and SQLite/PostgreSQL compatibility remain mandatory.
- Existing `materials.upload_platform` values are not rewritten and remain strings for backward compatibility.
- Platform names are trimmed, NFKC-normalized and compared case-insensitively; maximum length is 60 characters.
- No delete, rename, sort-management page, authentication, permissions, or background processing is added.
- Production code is written only after the corresponding test has failed for the expected reason.

---

### Task 1: Persistent catalog model, migration, repository and API

**Files:**
- Create: `backend/app/models/upload_platform.py`
- Create: `backend/app/schemas/upload_platform.py`
- Create: `backend/app/repositories/upload_platform_repository.py`
- Create: `backend/app/services/upload_platform_service.py`
- Create: `backend/app/api/endpoints/upload_platforms.py`
- Create: `backend/alembic/versions/20260812_0009_upload_platform_catalog.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/router.py`
- Test: `backend/tests/test_upload_platforms.py`
- Test: `backend/tests/test_upload_platform_migration.py`

**Interfaces:**
- Produces: `GET /api/upload-platforms -> ApiResponse[list[UploadPlatformRead]]`.
- Produces: `POST /api/upload-platforms` with `{ "name": string }`, returning HTTP 201 or normalized duplicate HTTP 409.
- Produces: `UploadPlatformRepository.list_active()`, `get_by_normalized_name()`, and `create()`.

- [ ] **Step 1: Write failing API tests**

```python
def test_create_platform_persists_and_lists_for_other_requests(client):
    created = client.post('/api/upload-platforms', json={'name': '  星河阅读  '})
    assert created.status_code == 201
    assert created.json()['data']['name'] == '星河阅读'
    assert '星河阅读' in [item['name'] for item in client.get('/api/upload-platforms').json()['data']]

def test_create_platform_rejects_normalized_duplicate(client):
    assert client.post('/api/upload-platforms', json={'name': 'Ｓｔａｒ'}).status_code == 201
    assert client.post('/api/upload-platforms', json={'name': 'star'}).status_code == 409
```

- [ ] **Step 2: Run the focused API tests and verify RED**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_upload_platforms.py -q`

Expected: FAIL because `/api/upload-platforms` does not exist.

- [ ] **Step 3: Implement the typed model, schemas, repository, service and endpoint**

```python
class UploadPlatform(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'upload_platforms'
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

def normalize_platform_name(value: str) -> tuple[str, str]:
    display = unicodedata.normalize('NFKC', value).strip()
    if not display:
        raise RequestValidationError('平台名称不能为空')
    return display, display.casefold()
```

The service must catch an existing normalized key and raise the project's 409 conflict exception. The list orders `is_system DESC, name ASC` and excludes soft-deleted rows.

- [ ] **Step 4: Run the focused API tests and verify GREEN**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_upload_platforms.py -q`

Expected: all focused tests pass.

- [ ] **Step 5: Write the failing migration test**

The test creates a temporary 0008 SQLite database containing an existing material with platform `历史站点`, upgrades to 0009, and asserts the catalog contains all built-ins plus `历史站点`; downgrade removes only the catalog table; upgrade again succeeds without modifying the material.

- [ ] **Step 6: Run the migration test and verify RED**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_upload_platform_migration.py -q`

Expected: FAIL because revision 0009 is absent.

- [ ] **Step 7: Implement migration 0009**

Create the table and indexes, insert the built-in names, then select distinct nonblank `materials.upload_platform` rows and insert any missing normalized key. Use deterministic UUID strings and UTC timestamps inside the migration. Downgrade drops the catalog table and does not touch materials.

- [ ] **Step 8: Run API and migration tests, then commit**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_upload_platforms.py tests/test_upload_platform_migration.py -q`

Commit: `feat: persist custom upload platforms`

---

### Task 2: Shared frontend platform catalog

**Files:**
- Create: `frontend/src/api/uploadPlatforms.ts`
- Create: `frontend/src/types/uploadPlatform.ts`
- Create: `frontend/src/stores/uploadPlatforms.ts`
- Modify: `frontend/src/components/material/UploadPlatformSelect.vue`
- Modify: `frontend/src/components/material/MaterialFilterBar.vue`
- Modify: `frontend/src/components/material/MaterialUploadDrawer.vue`
- Modify: `frontend/src/components/material/MaterialDetailDrawer.vue`
- Test: `frontend/src/__tests__/uploadPlatforms.spec.ts`

**Interfaces:**
- Consumes: backend list/create API from Task 1.
- Produces: `useUploadPlatformsStore()` with `platforms`, `loading`, `fetchPlatforms(force?)`, and `createPlatform(name)`.
- Produces: `UploadPlatformSelect` that persists on confirmation and emits the saved server spelling.

- [ ] **Step 1: Write failing store/component tests**

```ts
it('persists a custom platform and selects it', async () => {
  api.createUploadPlatform.mockResolvedValue({ id: 'p1', name: '星河阅读', is_system: false })
  const wrapper = mount(UploadPlatformSelect, { props: { modelValue: '' } })
  await wrapper.get('[data-test="add-custom-platform"]').trigger('click')
  await wrapper.get('[data-test="custom-platform-input"]').setValue(' 星河阅读 ')
  await wrapper.get('[data-test="confirm-custom-platform"]').trigger('click')
  expect(api.createUploadPlatform).toHaveBeenCalledWith('星河阅读')
  expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual(['星河阅读'])
})
```

Add tests proving a fresh selector reuses the store value, the filter receives the same catalog, and failed creation retains the input.

- [ ] **Step 2: Run the focused frontend test and verify RED**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/uploadPlatforms.spec.ts`

Expected: FAIL because API/store files and persistent behavior do not exist.

- [ ] **Step 3: Implement API, types and Pinia store**

```ts
export const useUploadPlatformsStore = defineStore('upload-platforms', () => {
  const platforms = ref<string[]>([...COMMON_UPLOAD_PLATFORMS])
  async function fetchPlatforms(force = false): Promise<void> {
    if (loaded.value && !force) return
    mergePlatforms((await listUploadPlatforms()).map((item) => item.name))
    loaded.value = true
  }
  async function createPlatform(name: string): Promise<string> {
    const created = await createUploadPlatform(name)
    mergePlatforms([created.name])
    return created.name
  }
  return { platforms, loading, fetchPlatforms, createPlatform }
})
```

Deduplicate with `trim().normalize('NFKC').toLocaleLowerCase()` and never replace the catalog with an empty list on a transient request failure.

- [ ] **Step 4: Wire all material controls to the shared store**

`UploadPlatformSelect` calls `fetchPlatforms()` on mount and awaits `createPlatform()` before closing the custom entry row. The filter and both drawers pass/store the shared options. On an API error, show the normalized API message and retain `customName`.

- [ ] **Step 5: Run focused tests and TypeScript check, then commit**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/uploadPlatforms.spec.ts src/__tests__/materialPlatform.spec.ts`

Run: `cd frontend; node .\node_modules\vue-tsc\bin\vue-tsc.js -b`

Commit: `feat: reuse saved platforms across material forms`

---

### Task 3: Include saved platforms in the positioning selector

**Files:**
- Modify: `frontend/src/stores/genrePositioning.ts`
- Modify: `frontend/src/__tests__/genrePositioning.spec.ts`

**Interfaces:**
- Consumes: `useUploadPlatformsStore().fetchPlatforms()` and `.platforms` from Task 2.
- Preserves: `全部平台` as the first option and current query/platform selection behavior.

- [ ] **Step 1: Write a failing positioning store test**

Mock the persistent catalog as `['抖音', '星河阅读']` while aggregate data contains only `抖音`; assert the selector becomes `['全部平台', '抖音', '星河阅读']` and selecting `星河阅读` calls the timeline API and displays an empty chart state.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/genrePositioning.spec.ts`

Expected: FAIL because the store currently derives platforms only from positioning data.

- [ ] **Step 3: Merge catalog and aggregate platform names**

Load the persistent platform store and positioning aggregate together, normalize/deduplicate the union, prepend `全部平台`, and preserve the preferred route platform when present.

- [ ] **Step 4: Run focused tests and commit**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/genrePositioning.spec.ts src/__tests__/uploadPlatforms.spec.ts`

Commit: `feat: show saved platforms in heat trends`

---

### Task 4: Seed integration, full verification and runtime handoff

**Files:**
- Modify: `backend/app/seed/run.py`
- Modify: `docs/PLATFORM_HEAT_TRENDS.md`
- Test: existing backend and frontend suites.

**Interfaces:**
- Consumes: repository/service behavior from Task 1.
- Produces: idempotent built-in platform catalog initialization in both migration and seed workflows.

- [ ] **Step 1: Add a failing idempotent seed test**

Run the existing seed entrypoint twice against a temporary database and assert the built-in platform count and normalized names are unchanged.

- [ ] **Step 2: Implement catalog seeding and verify focused tests**

Reuse the same built-in platform constant and normalization helper as the service; do not duplicate name rules.

- [ ] **Step 3: Run backend full verification**

Run: `cd backend; .\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp '..\.runtime\persistent-platform-backend'`

Run migration cycle only on a new temporary SQLite database: upgrade head, downgrade 0008, upgrade head, and `alembic check`.

- [ ] **Step 4: Run frontend full verification**

Run: `cd frontend; node .\node_modules\vue-tsc\bin\vue-tsc.js -b`

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run`

Run: `cd frontend; node .\node_modules\vite\bin\vite.js build`

- [ ] **Step 5: Upgrade only the portable runtime database with a verified backup**

Stop the running server, create and verify a backup with the project backup tool, load the same environment variables used by `start.bat`, run `alembic upgrade head`, then restart via `start.bat`. Do not modify the preserved original 0003 database.

- [ ] **Step 6: Perform runtime acceptance and commit documentation**

Create `星河阅读` through the API/UI, reopen the upload drawer, refresh the page and verify it remains available in upload, filter, and positioning selectors. Confirm `/api/health/ready` is ready and leave the service running.

Commit: `docs: document persistent upload platforms`
