<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Grid, List } from '@element-plus/icons-vue'
import GenreHeatTrendChart from '../components/genre-map/GenreHeatTrendChart.vue'
import GenrePositioningTable from '../components/genre-map/GenrePositioningTable.vue'
import { ALL_PLATFORMS, useGenrePositioningStore } from '../stores/genrePositioning'
import type { GenrePositioningTimelinePoint } from '../types/genrePositioning'

const route = useRoute()
const router = useRouter()
const store = useGenrePositioningStore()
const view = ref<'chart' | 'table'>((localStorage.getItem('genre-map-view') as 'chart' | 'table') || 'chart')

const genreCount = computed(() => new Set(store.timeline.points.map((point) => point.genre_module_id)).size)
const overallHeat = computed(() => {
  const count = store.timeline.points.reduce((sum, point) => sum + point.material_count, 0)
  return count
    ? store.timeline.points.reduce((sum, point) => sum + point.average_heat * point.material_count, 0) / count
    : 0
})

function routePlatform() {
  const value = route.query.upload_platform
  return typeof value === 'string' ? value : ''
}
function setView(next: 'chart' | 'table') {
  view.value = next
  localStorage.setItem('genre-map-view', next)
}
async function changePlatform(platform: string) {
  await store.selectPlatform(platform)
  await router.replace({ query: platform && platform !== ALL_PLATFORMS ? { upload_platform: platform } : {} })
}
function viewMaterials(point: GenrePositioningTimelinePoint) {
  const query: Record<string, string> = { genre_module_id: point.genre_module_id }
  if (store.selectedPlatform !== ALL_PLATFORMS) query.upload_platform = store.selectedPlatform
  void router.push({
    path: '/materials',
    query,
  })
}

watch(() => route.query.upload_platform, (value) => {
  const platform = typeof value === 'string' && value ? value : ALL_PLATFORMS
  if (platform !== store.selectedPlatform) void store.selectPlatform(platform)
})
onMounted(() => store.fetchPlatforms(routePlatform()))
</script>

<template>
  <div class="page-shell">
    <header class="page-heading">
      <div><span class="eyebrow">PLATFORM GENRE TRENDS</span><h1>题材平台热度趋势图</h1><p>选择全部平台查看总体趋势，或选择具体上传平台查看各题材的月度平均热度曲线。</p></div>
      <label class="platform-picker"><span>选择平台</span><el-select :model-value="store.selectedPlatform" filterable placeholder="请选择上传平台" @change="changePlatform"><el-option v-for="platform in store.platforms" :key="platform" :label="platform" :value="platform" /></el-select></label>
    </header>

    <section class="summary">
      <div><small>当前范围</small><b class="platform-name">{{ store.selectedPlatform || '—' }}</b><span>统计范围</span></div>
      <div><small>覆盖题材</small><b>{{ genreCount }}</b><span>种题材类型</span></div>
      <div><small>覆盖月份</small><b>{{ store.timeline.periods.length }}</b><span>个有效月份</span></div>
      <div><small>整体平均热度</small><b>{{ overallHeat.toFixed(1) }}</b><span>按素材数量加权</span></div>
    </section>

    <section class="trend-panel surface">
      <header><div><h2>{{ store.selectedPlatform || '平台' }} · 各题材月度热度</h2><p>每条曲线代表一个题材；没有素材的月份保留空档，不按零计算。</p></div><div class="view-switch"><button :class="{ active: view === 'chart' }" @click="setView('chart')"><el-icon><Grid /></el-icon>图表</button><button :class="{ active: view === 'table' }" @click="setView('table')"><el-icon><List /></el-icon>表格</button></div></header>
      <GenreHeatTrendChart v-if="view === 'chart'" :timeline="store.timeline" :loading="store.loading" :error="store.error" @select="viewMaterials" @retry="store.fetchPlatforms(store.selectedPlatform)" />
      <GenrePositioningTable v-else :points="store.timeline.points" :upload-platform="store.selectedPlatform" :loading="store.loading" @view="viewMaterials" />
    </section>
  </div>
</template>

<style scoped>
.page-shell{max-width:1600px;margin:0 auto;padding:30px 32px 52px}.page-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-bottom:18px}.eyebrow{color:var(--accent);font-size:10px;font-weight:800;letter-spacing:.18em}.page-heading h1{margin:7px 0 6px;font-family:"Songti SC",serif;font-size:30px}.page-heading p{margin:0;color:var(--text-muted);font-size:13px}.platform-picker{width:min(360px,34vw);display:grid;gap:7px}.platform-picker span{color:var(--text-secondary);font-size:13px;font-weight:700}.platform-picker :deep(.el-select){width:100%}.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px}.summary>div{min-height:82px;padding:17px 18px;border:1px solid var(--border-soft);border-radius:10px;background:var(--panel)}.summary small,.summary span{color:var(--text-muted);font-size:11px}.summary b{display:inline-block;margin:0 9px 0 16px;font-size:24px}.summary .platform-name{max-width:160px;overflow:hidden;text-overflow:ellipsis;vertical-align:middle;white-space:nowrap;font-size:17px}.trend-panel{border-radius:11px;overflow:hidden}.trend-panel>header{min-height:72px;display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--border-soft)}.trend-panel h2{margin:0;font-size:15px}.trend-panel header p{margin:6px 0 0;color:var(--text-muted);font-size:12px}.view-switch{display:flex;padding:4px;border:1px solid var(--border);border-radius:8px;background:var(--bg-soft)}.view-switch button{display:flex;align-items:center;gap:6px;padding:7px 11px;border:0;border-radius:6px;background:transparent;color:var(--text-muted);font-size:12px;cursor:pointer}.view-switch button.active{background:var(--panel-hover);color:var(--accent)}@media(max-width:900px){.page-heading{align-items:stretch;flex-direction:column}.platform-picker{width:100%}.summary{grid-template-columns:repeat(2,1fr)}}
</style>
