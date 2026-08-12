<script setup lang="ts">
import { computed, ref } from 'vue'
import { PLATFORM_HEAT_RATINGS, getPlatformHeatRating } from '../../utils/platformHeatRating'

const model = defineModel<number | null | undefined>({ required: true })
const props = withDefaults(defineProps<{ testId?: string }>(), { testId: 'platform-heat' })
const pointerInside = ref(false)
const focusInside = ref(false)
const guideOpen = computed(() => pointerInside.value || focusInside.value)
const currentRating = computed(() => getPlatformHeatRating(model.value))
</script>

<template>
  <div
    class="platform-heat-input"
    :data-test="`${testId}-field`"
    @mouseenter="pointerInside = true"
    @mouseleave="pointerInside = false"
    @focusin="focusInside = true"
    @focusout="focusInside = false"
  >
    <el-input-number
      v-model="model"
      :data-test="testId"
      :min="0"
      :max="100"
      :step="1"
      class="heat-number"
      placeholder="0 到 100"
    />

    <div v-if="currentRating" data-test="heat-current-rating" class="current-rating" :class="`rating--${currentRating.tone}`">
      <b>{{ model }} · {{ currentRating.name }}</b>
      <span>{{ currentRating.advice }}</span>
    </div>
    <small v-else class="rating-hint">将鼠标移入或点击输入框查看评分标准</small>

    <aside v-if="guideOpen" data-test="heat-rating-guide" class="rating-guide" role="note" aria-label="平台热度评分标准">
      <header><b>平台热度评分标准</b><span>请根据素材表现自行判断</span></header>
      <div
        v-for="rating in PLATFORM_HEAT_RATINGS"
        :key="rating.name"
        data-test="heat-rating-row"
        class="rating-row"
        :class="[`rating--${rating.tone}`, { 'is-current': currentRating?.name === rating.name }]"
      >
        <strong>{{ rating.rangeLabel }}</strong>
        <b>{{ rating.name }}</b>
        <span>{{ rating.advice }}</span>
        <em v-if="currentRating?.name === rating.name">当前</em>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.platform-heat-input{position:relative;width:100%}.heat-number{width:100%}.current-rating{display:flex;align-items:center;gap:8px;margin-top:7px;padding:7px 10px;border:1px solid currentColor;border-radius:7px;background:color-mix(in srgb,currentColor 8%,transparent);font-size:12px;line-height:1.4}.current-rating b{white-space:nowrap}.current-rating span{color:var(--text-muted)}.rating-hint{display:block;margin-top:6px;color:var(--text-muted);font-size:11px}.rating-guide{position:absolute;z-index:40;top:calc(100% + 8px);right:0;width:min(520px,calc(100vw - 48px));padding:12px;border:1px solid var(--border);border-radius:10px;background:var(--panel-raised);box-shadow:0 16px 38px rgb(15 23 42 / 20%)}.rating-guide::before{position:absolute;top:-6px;right:24px;width:11px;height:11px;border-top:1px solid var(--border);border-left:1px solid var(--border);background:var(--panel-raised);content:'';transform:rotate(45deg)}.rating-guide header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:2px 3px 10px}.rating-guide header b{color:var(--text);font-size:13px}.rating-guide header span{color:var(--text-muted);font-size:11px}.rating-row{position:relative;display:grid;grid-template-columns:72px 82px 1fr auto;align-items:center;gap:8px;min-height:38px;padding:7px 9px;border:1px solid transparent;border-radius:7px;color:var(--text-secondary);font-size:12px}.rating-row strong{color:currentColor;font-variant-numeric:tabular-nums}.rating-row b{color:var(--text)}.rating-row span{color:var(--text-muted)}.rating-row em{padding:2px 6px;border-radius:999px;background:currentColor;color:#fff;font-size:10px;font-style:normal}.rating-row.is-current{border-color:currentColor;background:color-mix(in srgb,currentColor 10%,transparent)}.rating--excellent{color:#ef4444}.rating--good{color:#f97316}.rating--normal{color:#eab308}.rating--weak{color:#3b82f6}.rating--discard{color:#64748b}@media(max-width:600px){.rating-guide{right:auto;left:0;width:min(420px,calc(100vw - 40px))}.rating-guide::before{right:auto;left:24px}.rating-guide header{align-items:flex-start;flex-direction:column;gap:3px}.rating-row{grid-template-columns:62px 74px 1fr}.rating-row em{display:none}}
</style>
