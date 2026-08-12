# Platform Heat Rating Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a five-level scoring guide whenever an uploader enters platform heat, highlight the current level live, and keep saving only the original 0–100 number.

**Architecture:** Put rating thresholds and classification in one pure TypeScript module, then render them through a reusable controlled `PlatformHeatInput` component. Replace the existing Element Plus number controls in upload and edit drawers without changing API payloads, backend validation, database schema, or trend aggregation.

**Tech Stack:** Vue 3, TypeScript, Element Plus, Vitest, Vue Test Utils, Vite.

## Global Constraints

- The database continues to store only `platform_heat`; no migration or backend contract change.
- Rating intervals are `[85,100]`, `[70,85)`, `[50,70)`, `[30,50)`, and `[0,30)`.
- Display labels remain `85～100`, `70～84`, `50～69`, `30～49`, and `0～29`.
- Zero is a valid score and must not be treated as empty.
- No relative scoring, same-period average, weighting, or automatic score adjustment.
- The user will perform browser acceptance; implementation verification is limited to focused automated tests, TypeScript checking, and production build.

---

### Task 1: Rating model and reusable input component

**Files:**
- Create: `frontend/src/utils/platformHeatRating.ts`
- Create: `frontend/src/components/material/PlatformHeatInput.vue`
- Create: `frontend/src/__tests__/platformHeatRating.spec.ts`

**Interfaces:**
- Produces: `PLATFORM_HEAT_RATINGS: readonly PlatformHeatRating[]` ordered high to low.
- Produces: `getPlatformHeatRating(value: number | null | undefined): PlatformHeatRating | null`.
- Produces: `PlatformHeatInput` with required `v-model<number | null | undefined>` and optional `testId`.

- [ ] **Step 1: Write failing boundary tests**

```ts
expect(getPlatformHeatRating(null)).toBeNull()
expect(getPlatformHeatRating(0)?.name).toBe('淘汰素材')
expect(getPlatformHeatRating(29.9)?.name).toBe('淘汰素材')
expect(getPlatformHeatRating(30)?.name).toBe('低效素材')
expect(getPlatformHeatRating(50)?.name).toBe('普通素材')
expect(getPlatformHeatRating(70)?.name).toBe('优质素材')
expect(getPlatformHeatRating(85)?.name).toBe('超级爆款')
expect(getPlatformHeatRating(100)?.name).toBe('超级爆款')
expect(getPlatformHeatRating(101)).toBeNull()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/platformHeatRating.spec.ts`

Expected: FAIL because the rating module and component do not exist.

- [ ] **Step 3: Implement rating configuration and classifier**

```ts
export interface PlatformHeatRating {
  min: number
  max: number
  rangeLabel: string
  name: string
  advice: string
  tone: 'excellent' | 'good' | 'normal' | 'weak' | 'discard'
}

export function getPlatformHeatRating(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value) || value < 0 || value > 100) return null
  return PLATFORM_HEAT_RATINGS.find((rating) => value >= rating.min && value <= rating.max) ?? null
}
```

Use non-overlapping decimal-safe maximums by checking the list in descending order and declaring lower bands with the next threshold excluded.

- [ ] **Step 4: Write the failing component interaction tests**

Mount the real component with Element Plus input-number stub. Assert hover or focus reveals all five rows, 88 highlights `超级爆款`, 0 highlights `淘汰素材`, and empty input has no `.is-current` row.

- [ ] **Step 5: Implement the controlled component**

The wrapper opens on `mouseenter`, `focusin`, or click; closes after both pointer and focus leave. It renders `el-input-number` with `min=0`, `max=100`, `step=1`, emits the original numeric value, shows the current compact result, and uses text plus tone classes for accessibility.

- [ ] **Step 6: Run the focused test and commit**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/platformHeatRating.spec.ts`

Commit: `feat: add platform heat rating guide`

---

### Task 2: Integrate upload and edit forms

**Files:**
- Modify: `frontend/src/components/material/MaterialUploadDrawer.vue`
- Modify: `frontend/src/components/material/MaterialDetailDrawer.vue`
- Modify: `frontend/src/__tests__/materialPlatform.spec.ts`
- Modify: `frontend/src/__tests__/sprint3.materials.spec.ts`

**Interfaces:**
- Consumes: `PlatformHeatInput` from Task 1.
- Preserves: upload payload `platform_heat: number` and edit payload `platform_heat: number | null`.

- [ ] **Step 1: Write failing integration tests**

Assert both drawers contain `PlatformHeatInput`; set upload heat to 88 and edit heat to 0 through the component `update:modelValue` event, submit using the existing form flow, and assert the unchanged numeric payloads.

- [ ] **Step 2: Run the two focused files and verify RED**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/platformHeatRating.spec.ts src/__tests__/materialPlatform.spec.ts src/__tests__/sprint3.materials.spec.ts`

Expected: FAIL because both drawers still render `el-input-number` directly.

- [ ] **Step 3: Replace both direct number controls**

```vue
<PlatformHeatInput v-model="platformHeat" test-id="platform-heat" />
<PlatformHeatInput v-model="form.platform_heat" test-id="edit-heat" />
```

Do not alter existing validation, API serialization, required-field behavior, or reset behavior.

- [ ] **Step 4: Run focused verification**

Run: `cd frontend; node .\node_modules\vitest\vitest.mjs run src/__tests__/platformHeatRating.spec.ts src/__tests__/materialPlatform.spec.ts src/__tests__/sprint3.materials.spec.ts`

Run: `cd frontend; node .\node_modules\vue-tsc\bin\vue-tsc.js -b`

Run: `cd frontend; node .\node_modules\vite\bin\vite.js build`

- [ ] **Step 5: Commit and restart the existing service**

Commit: `feat: guide platform heat scoring in material forms`

Stop only the confirmed project process listening on port 8000, then launch `D:\文档存储\start.bat`. Confirm only `/api/health/ready` returns `ready`; leave browser interaction to the user.
