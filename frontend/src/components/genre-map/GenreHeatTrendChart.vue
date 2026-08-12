<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import type { GenrePositioningTimeline, GenrePositioningTimelinePoint } from '../../types/genrePositioning'
import { buildGenreHeatTrendOption, type ChartDatum } from '../../utils/genreHeatTrend'

const props = defineProps<{ timeline: GenrePositioningTimeline; loading?: boolean; error?: string | null }>()
const emit = defineEmits<{ select: [point: GenrePositioningTimelinePoint]; retry: [] }>()
const root = ref<HTMLDivElement>()
const initError = ref('')
let chart: ECharts | undefined
let observer: ResizeObserver | undefined
let frame: number | undefined

function render() { chart?.setOption(buildGenreHeatTrendOption(props.timeline), true) }
function initializeChart() {
  if (chart || !root.value || root.value.clientWidth <= 0 || root.value.clientHeight <= 0) return
  try {
    chart = echarts.init(root.value)
    chart.on('click', (params: unknown) => {
      const point = (params as { data?: ChartDatum }).data?.raw
      if (point) emit('select', point)
    })
    render()
  } catch (reason) {
    initError.value = reason instanceof Error ? reason.message : '图表初始化失败'
  }
}
async function init() {
  await nextTick()
  if (!root.value) return
  observer = new ResizeObserver(() => { if (chart) chart.resize(); else initializeChart() })
  observer.observe(root.value)
  initializeChart()
  frame = requestAnimationFrame(initializeChart)
}

onMounted(init)
onBeforeUnmount(() => {
  if (frame !== undefined) cancelAnimationFrame(frame)
  observer?.disconnect()
  chart?.dispose()
})
watch(() => props.timeline, render, { deep: true })
</script>

<template>
  <div class="chart-wrap">
    <div v-if="error || initError" class="chart-state error">
      <b>图表加载失败</b><span>{{ error || initError }}</span><el-button :icon="Refresh" @click="emit('retry')">重新加载</el-button>
    </div>
    <div v-else-if="!loading && !timeline.points.length" class="chart-state">
      <b>当前平台暂无热度数据</b><span>上传或补充素材的平台与热度后，题材曲线会自动出现。</span>
    </div>
    <div v-show="!error && !initError && timeline.points.length" ref="root" v-loading="loading" class="chart-canvas"></div>
    <footer><span>每条曲线代表一个题材</span><em>横轴 = 上传月份 · 纵轴 = 平均热度 · 缺失月份不补零</em></footer>
  </div>
</template>

<style scoped>
.chart-wrap{position:relative}.chart-canvas{width:100%;height:620px}.chart-state{height:620px;display:grid;justify-items:center;align-content:center;gap:10px}.chart-state b{font-size:16px}.chart-state span{color:var(--text-muted);font-size:13px}.chart-state.error b{color:var(--danger)}.chart-wrap footer{min-height:48px;display:flex;align-items:center;justify-content:center;gap:20px;border-top:1px solid var(--border-soft);color:var(--text-secondary);font-size:12px}.chart-wrap footer em{color:var(--text-muted);font-style:normal}
</style>
