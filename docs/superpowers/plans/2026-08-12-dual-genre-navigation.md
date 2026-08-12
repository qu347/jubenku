# Dual Genre Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add separate “素材题材库” and “剧本题材库” dropdowns, genre-specific material/script pages, and a two-column configuration page with independent visibility and ordering.

**Architecture:** Keep one `GenreModule` identity per genre and add per-library navigation fields. The content table remains shared and continues using `Material.library_type` for strict material/script isolation. Frontend routes explicitly encode which library is being viewed, while management APIs accept a validated `library_type` for navigation filtering and reordering.

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, Alembic, SQLite, Pydantic; Vue 3, TypeScript, Vue Router, Pinia, Element Plus, Vitest.

## Global Constraints

- Keep the fixed top-level “素材库” and “剧本库” navigation entries unchanged.
- Use the names “素材题材库” and “剧本题材库” for the two dynamic dropdown groups.
- A genre keeps one shared name, slug, icon, theme color, description and global status.
- Material/script visibility and ordering are independent.
- Material queries use `library_type=material`; script queries use `library_type=script`.
- Do not add script review, versioning, collaboration or publishing workflows.
- Do not mutate protected source databases in tests; use isolated temporary SQLite databases.

---

### Task 1: Persist per-library genre navigation settings

**Files:**
- Create: `backend/alembic/versions/20260812_0007_dual_genre_navigation.py`
- Modify: `backend/app/models/genre.py`
- Modify: `backend/app/schemas/genre.py`
- Modify: `backend/app/repositories/genre_repository.py`
- Modify: `backend/app/services/genre_service.py`
- Modify: `backend/app/api/endpoints/genre_modules.py`
- Test: `backend/tests/test_genre_modules.py`
- Test: `backend/tests/test_sprint3_migration.py`

**Interfaces:**
- `GenreLibraryType = Literal["material", "script"]`
- `GET /api/genre-modules?library_type=material|script`
- `PATCH /api/genre-modules/batch/reorder?library_type=material|script`
- `GenreModuleRead` adds `material_visible`, `script_visible`, `material_sort_order`, `script_sort_order`, and `script_count`.

- [ ] **Step 1: Write failing API tests for independent navigation lists**

```python
def test_genre_navigation_is_filtered_and_sorted_per_library(client, db_session):
    first = create_module(db_session, name="西方奇幻", slug="western-fantasy")
    second = create_module(db_session, name="东方仙侠", slug="eastern-xianxia")
    first.material_visible = True
    first.script_visible = False
    first.material_sort_order = 1
    second.material_visible = True
    second.script_visible = True
    second.material_sort_order = 0
    second.script_sort_order = 3
    db_session.commit()

    materials = client.get("/api/genre-modules", params={"library_type": "material"})
    scripts = client.get("/api/genre-modules", params={"library_type": "script"})

    assert [item["slug"] for item in materials.json()["data"]] == ["eastern-xianxia", "western-fantasy"]
    assert [item["slug"] for item in scripts.json()["data"]] == ["eastern-xianxia"]
    assert client.get("/api/genre-modules", params={"library_type": "unknown"}).status_code == 422
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/test_genre_modules.py -q -p no:cacheprovider --basetemp=../.runtime/pytest_dual_genre_red`

Expected: FAIL because the model and API do not expose per-library navigation fields.

- [ ] **Step 3: Add the model, schemas, repository and API behavior**

```python
# backend/app/models/genre.py
material_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False, index=True)
script_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False, index=True)
material_sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, index=True)
script_sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, index=True)
```

`GenreRepository.list_modules()` must choose the matching visible and sort columns when `library_type` is present. Management calls with `include_hidden=True` return every module. `GenreService.reorder_modules(payload, library_type)` updates only the target sort column. Creation and duplication initialize both sides from the existing `visible` and `sort_order` values.

- [ ] **Step 4: Add migration 0007 and migration assertions**

The upgrade adds four columns and indexes, then copies legacy values:

```python
op.execute("UPDATE genre_modules SET material_visible = visible, script_visible = visible")
op.execute("UPDATE genre_modules SET material_sort_order = sort_order, script_sort_order = sort_order")
```

The migration test must insert at least two modules at 0006, upgrade to head, and assert all four values match legacy values without modifying names, slugs, materials or metrics.

- [ ] **Step 5: Run focused backend tests and verify GREEN**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/test_genre_modules.py tests/test_sprint3_migration.py -q -p no:cacheprovider --basetemp=../.runtime/pytest_dual_genre_green`

Expected: PASS.

- [ ] **Step 6: Commit the backend navigation model**

```bash
git add backend/alembic/versions/20260812_0007_dual_genre_navigation.py backend/app/models/genre.py backend/app/schemas/genre.py backend/app/repositories/genre_repository.py backend/app/services/genre_service.py backend/app/api/endpoints/genre_modules.py backend/tests/test_genre_modules.py backend/tests/test_sprint3_migration.py
git commit -m "feat: add per-library genre navigation settings"
```

---

### Task 2: Add explicit material and script genre routes

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/GenreModuleView.vue`
- Modify: `frontend/src/types/genreModule.ts`
- Modify: `frontend/src/api/genreModules.ts`
- Test: `frontend/src/__tests__/genreModuleView.spec.ts`

**Interfaces:**
- Material route: `/genres/:slug`, route name `genre-materials`, prop `libraryType="material"`.
- Script route: `/script-genres/:slug`, route name `genre-scripts`, prop `libraryType="script"`.
- `listGenreModules({ library_type })` accepts `'material' | 'script'`.

- [ ] **Step 1: Write failing genre-page isolation tests**

```ts
it('题材素材页只请求 material', async () => {
  mountGenreView('/genres/western-fantasy', 'material')
  await flushPromises()
  expect(apiMocks.listMaterials).toHaveBeenCalledWith(expect.objectContaining({
    genre_module_id: 'western-id', library_type: 'material',
  }))
})

it('题材剧本页只请求 script 并显示添加剧本', async () => {
  const wrapper = mountGenreView('/script-genres/western-fantasy', 'script')
  await flushPromises()
  expect(apiMocks.listMaterials).toHaveBeenCalledWith(expect.objectContaining({
    genre_module_id: 'western-id', library_type: 'script',
  }))
  expect(wrapper.text()).toContain('添加剧本')
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd frontend && pnpm run test:unit -- src/__tests__/genreModuleView.spec.ts`

Expected: FAIL because `GenreModuleView` has no `libraryType` prop and script route.

- [ ] **Step 3: Implement explicit routes and library-aware page copy**

Add `libraryType` as a required route prop with a default of `material` for compatibility. Pass it to list, upload and detail calls/components. Watch both `route.params.slug` and the prop so switching between material and script pages reloads data. Use “添加素材/素材标题” for material and “添加剧本/剧本标题” for script.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `cd frontend && pnpm run test:unit -- src/__tests__/genreModuleView.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit the genre routes**

```bash
git add frontend/src/router/index.ts frontend/src/views/GenreModuleView.vue frontend/src/types/genreModule.ts frontend/src/api/genreModules.ts frontend/src/__tests__/genreModuleView.spec.ts
git commit -m "feat: add material and script genre pages"
```

---

### Task 3: Replace the single sidebar picker with two named pickers

**Files:**
- Modify: `frontend/src/stores/genreModules.ts`
- Modify: `frontend/src/components/module/AppLayout.vue`
- Test: `frontend/src/__tests__/navigation.spec.ts`
- Test: `frontend/src/__tests__/genreModules.store.spec.ts`

**Interfaces:**
- Store state: `materialModules: GenreModule[]`, `scriptModules: GenreModule[]`.
- Store method: `fetchNavigationModules()` requests both library lists.
- Sidebar labels: “素材题材库” and “剧本题材库”.

- [ ] **Step 1: Write failing store and sidebar tests**

```ts
it('分别加载素材题材和剧本题材', async () => {
  api.listGenreModules
    .mockResolvedValueOnce([{ id: 'm1', slug: 'western-fantasy', name: '西方奇幻' }])
    .mockResolvedValueOnce([{ id: 's1', slug: 'urban-daily', name: '都市日常' }])
  const store = useGenreModulesStore()
  await store.fetchNavigationModules()
  expect(api.listGenreModules).toHaveBeenNthCalledWith(1, { library_type: 'material' })
  expect(api.listGenreModules).toHaveBeenNthCalledWith(2, { library_type: 'script' })
})

it('显示两个题材下拉框和正确链接', async () => {
  const wrapper = mountLayout()
  await flushPromises()
  expect(wrapper.text()).toContain('素材题材库')
  expect(wrapper.text()).toContain('剧本题材库')
  expect(wrapper.find('a[href="/genres/western-fantasy"]').exists()).toBe(true)
  expect(wrapper.find('a[href="/script-genres/urban-daily"]').exists()).toBe(true)
})
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `cd frontend && pnpm run test:unit -- src/__tests__/genreModules.store.spec.ts src/__tests__/navigation.spec.ts`

Expected: FAIL because only one `modules` list and picker exist.

- [ ] **Step 3: Implement two independent navigation lists and popovers**

Keep separate open state and current-module computed value for each picker. The material picker links to `/genres/${slug}`; the script picker links to `/script-genres/${slug}`. In collapsed mode both remain icon buttons with accessible labels. Empty/error state remains compact and retry reloads both lists.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `cd frontend && pnpm run test:unit -- src/__tests__/genreModules.store.spec.ts src/__tests__/navigation.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit the dual sidebar navigation**

```bash
git add frontend/src/stores/genreModules.ts frontend/src/components/module/AppLayout.vue frontend/src/__tests__/genreModules.store.spec.ts frontend/src/__tests__/navigation.spec.ts
git commit -m "feat: add dual genre library pickers"
```

---

### Task 4: Restore a two-column genre configuration page

**Files:**
- Modify: `frontend/src/views/settings/ModuleSettingsView.vue`
- Modify: `frontend/src/stores/genreModules.ts`
- Modify: `frontend/src/api/genreModules.ts`
- Test: `frontend/src/__tests__/sprint3.navigation.spec.ts`

**Interfaces:**
- `updateModule(id, { material_visible })` and `updateModule(id, { script_visible })` update one side.
- `reorderGenreModules(items, libraryType)` sends the validated query parameter.
- Desktop layout: two equal columns; under 1180px: stacked material then script.

- [ ] **Step 1: Write failing settings-layout behavior tests**

```ts
it('题材配置显示素材和剧本双栏', async () => {
  const wrapper = mount(ModuleSettingsView)
  await flushPromises()
  expect(wrapper.find('[data-testid="material-genre-config"]').exists()).toBe(true)
  expect(wrapper.find('[data-testid="script-genre-config"]').exists()).toBe(true)
  expect(wrapper.text()).toContain('素材题材配置')
  expect(wrapper.text()).toContain('剧本题材配置')
})

it('剧本侧显示开关只更新 script_visible', async () => {
  const wrapper = mount(ModuleSettingsView)
  await flushPromises()
  wrapper.find('[data-testid="script-genre-config"] .el-switch').trigger('change')
  expect(api.updateGenreModule).toHaveBeenCalledWith('genre-id', { script_visible: false })
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd frontend && pnpm run test:unit -- src/__tests__/sprint3.navigation.spec.ts`

Expected: FAIL because the settings page renders one full-width list.

- [ ] **Step 3: Extract one local reusable panel and render it twice**

Within `ModuleSettingsView.vue`, use a typed panel descriptor rather than duplicating mutation logic:

```ts
type ConfigSide = {
  libraryType: 'material' | 'script'
  title: string
  visibleKey: 'material_visible' | 'script_visible'
  sortKey: 'material_sort_order' | 'script_sort_order'
}
```

Both panels show the shared genre identity and global status. Each panel owns its visibility switch, drag order and move buttons. Global edit/enable/duplicate/delete actions can appear in both menus but call the same existing operation.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `cd frontend && pnpm run test:unit -- src/__tests__/sprint3.navigation.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit the two-column configuration page**

```bash
git add frontend/src/views/settings/ModuleSettingsView.vue frontend/src/stores/genreModules.ts frontend/src/api/genreModules.ts frontend/src/__tests__/sprint3.navigation.spec.ts
git commit -m "feat: split genre settings into material and script columns"
```

---

### Task 5: Documentation, full verification and running-data migration

**Files:**
- Modify: `README.md`
- Modify: `docs/PRODUCT_SPEC.md`
- Modify: `docs/USER_GUIDE.md`
- Generated: `frontend/dist/**`

**Interfaces:**
- One-click startup continues through `start.bat` and Alembic `upgrade head`.
- Running page checks: `/materials`, `/scripts`, `/genres/western-fantasy`, `/script-genres/western-fantasy`.

- [ ] **Step 1: Update user-facing documentation**

Document the two picker names, route responsibilities, shared genre identity, independent visibility/order, and two-column settings page. Remove statements that imply the single picker only serves materials.

- [ ] **Step 2: Run full backend verification**

Run:

```powershell
cd backend
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp='D:\文档存储\.runtime\pytest_dual_genre_final'
.\.venv\Scripts\alembic.exe check
```

Expected: all tests pass and `No new upgrade operations detected.`

- [ ] **Step 3: Run full frontend verification and build**

Run:

```powershell
cd frontend
pnpm run type-check
pnpm run test:unit
pnpm run build
```

Expected: type-check passes, all tests pass, production build succeeds.

- [ ] **Step 4: Upgrade only the running portable database and restart**

Stop the verified process listening on `127.0.0.1:8000`, then launch `start.bat`. Confirm the existing material count is unchanged, migration head is `20260812_0007`, and script data remains separate.

- [ ] **Step 5: Smoke-test live routes and APIs**

Verify:

```text
GET /api/genre-modules?library_type=material -> 200
GET /api/genre-modules?library_type=script   -> 200
GET /api/genre-modules?library_type=unknown  -> 422
GET /genres/western-fantasy                  -> 200 SPA
GET /script-genres/western-fantasy           -> 200 SPA
```

The sidebar must show both named pickers, and settings must show two columns on desktop.

- [ ] **Step 6: Commit documentation and release build metadata**

```bash
git add README.md docs/PRODUCT_SPEC.md docs/USER_GUIDE.md
git commit -m "docs: document dual genre libraries"
```
