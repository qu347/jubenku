<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import type { EducationLevel, GenreMetric } from '../../types/genreMetric'
import { AGE_LABEL, bubbleSize, EDUCATION_LABEL, EDUCATION_SCORE, regionShare, weightedMean } from '../../utils/genreMap'

const props = defineProps<{ items: GenreMetric[]; loading?: boolean; error?: string | null }>()
const emit = defineEmits<{ select: [metric: GenreMetric]; retry: [] }>()
const root = ref<HTMLDivElement>()
const initError = ref('')
let chart: ECharts | undefined
let observer: ResizeObserver | undefined
let frame: number | undefined

const averageAge = computed(() => weightedMean(props.items, (item) => item.average_age))
const averageEducation = computed(() => weightedMean(props.items, (item) => EDUCATION_SCORE[item.education_level]))
const ages = [{ key: 'youth', from: 12, to: 22.99 }, { key: 'middle', from: 23, to: 50.99 }, { key: 'senior', from: 51, to: 100 }] as const
const educations: [EducationLevel, number][] = [['low', 1], ['medium', 2], ['high', 3]]

function metricName(item: GenreMetric) { return item.genre_module?.name || item.genre_name || '未命名题材' }
function tooltipText(params: unknown) {
  const item = (params as { data?: { raw?: GenreMetric } }).data?.raw
  if (!item) return ''
  return [
    metricName(item),
    `平均年龄：${item.average_age} 岁`,
    `年龄层级：${AGE_LABEL[item.age_group]}`,
    `学历层级：${EDUCATION_LABEL[item.education_level]}`,
    `用户占比：${item.audience_share}%`,
    `热度指数：${item.heat_index}`,
    `平台 / 频道：${item.platform} / ${item.channel}`,
    `周期：${item.period}`,
    `趋势：${{ rising: '上升', stable: '稳定', falling: '下降' }[item.trend]}`,
    `样本量：${item.sample_size.toLocaleString()}`,
    `来源：${item.data_source || '—'}`,
  ].join('\n')
}

function option(): EChartsOption {
  const areas = ages.flatMap((age, ageIndex) => educations.map(([education, y], educationIndex) => [
    {
      name: `${AGE_LABEL[age.key]} × ${EDUCATION_LABEL[education]}\n区域占比 ${regionShare(props.items, age.key, education).toFixed(1)}%`,
      xAxis: age.from,
      yAxis: y - .49,
      itemStyle: { color: (ageIndex + educationIndex) % 2 ? 'rgba(31,49,76,.14)' : 'rgba(18,36,60,.24)' },
    },
    { xAxis: age.to, yAxis: y + .49 },
  ] as [{ name: string; xAxis: number; yAxis: number; itemStyle: { color: string } }, { xAxis: number; yAxis: number }]))

  return {
    backgroundColor: 'transparent',
    animationDuration: 420,
    grid: { left: 75, right: 40, top: 35, bottom: 64 },
    tooltip: {
      trigger: 'item',
      renderMode: 'richText',
      backgroundColor: '#111a2d',
      borderColor: '#334155',
      textStyle: { color: '#eef2f8', fontSize: 11, lineHeight: 18 },
      formatter: tooltipText,
    },
    xAxis: { type: 'value', min: 12, max: 100, name: '平均年龄', nameLocation: 'middle', nameGap: 38, axisLabel: { color: '#7f8da5' }, axisLine: { lineStyle: { color: '#43506a' } }, splitLine: { show: false } },
    yAxis: { type: 'value', min: .5, max: 3.5, interval: 1, name: '学历层级', axisLabel: { color: '#7f8da5', formatter: (value: number) => ({ 1: '低学历', 2: '中学历', 3: '高学历' }[value] || '') }, axisLine: { lineStyle: { color: '#43506a' } }, splitLine: { show: false } },
    series: [{
      type: 'scatter',
      z: 4,
      data: props.items.map((item) => ({
        value: [item.average_age, EDUCATION_SCORE[item.education_level], item.audience_share],
        raw: item,
        name: metricName(item),
        symbolSize: bubbleSize(item.audience_share),
        itemStyle: { color: { low: '#a78bfa', medium: '#34d399', high: '#60a5fa' }[item.education_level], borderColor: item.is_core ? '#f59e0b' : 'rgba(255,255,255,.42)', borderWidth: item.is_core ? 3 : 1, opacity: .88 },
      })),
      label: { show: true, formatter: '{b}', color: '#f8fafc', fontSize: 9, fontWeight: 700 },
      emphasis: { scale: 1.12 },
      markLine: { silent: true, symbol: 'none', lineStyle: { color: '#f97316', type: 'dashed', width: 1.5 }, label: { color: '#fb923c', fontSize: 9 }, data: props.items.length ? [{ xAxis: averageAge.value, name: `加权年龄 ${averageAge.value.toFixed(1)}` }, { yAxis: averageEducation.value, name: `加权学历 ${averageEducation.value.toFixed(2)}` }] : [] },
      markArea: { silent: true, z: 0, itemStyle: { borderColor: 'rgba(80,100,130,.32)', borderWidth: 1 }, label: { show: true, position: 'insideTopLeft', color: '#64748b', fontSize: 8, lineHeight: 13 }, data: areas },
    }],
  }
}

function render() { chart?.setOption(option(), true) }
function initializeChart() {
  if (chart || !root.value || root.value.clientWidth <= 0 || root.value.clientHeight <= 0) return
  try {
    chart = echarts.init(root.value)
    chart.on('click', (params: unknown) => {
      const item = (params as { data?: { raw?: GenreMetric } }).data?.raw
      if (item) emit('select', item)
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
onBeforeUnmount(() => { if (frame !== undefined) cancelAnimationFrame(frame); observer?.disconnect(); chart?.dispose() })
watch(() => props.items, render, { deep: true })
</script>

<template>
  <div class="chart-wrap">
    <div v-if="error || initError" class="chart-state error"><b>图表加载失败</b><span>{{ error || initError }}</span><el-button :icon="Refresh" @click="emit('retry')">重新加载</el-button></div>
    <div v-else-if="!loading && !items.length" class="chart-state"><b>暂无定位数据</b><span>新增或导入数据后，气泡会立即出现在九宫格中。</span></div>
    <div v-show="!error && !initError && items.length" ref="root" v-loading="loading" class="chart-canvas"></div>
    <footer><span><i class="high"></i>高学历</span><span><i class="medium"></i>中学历</span><span><i class="low"></i>低学历</span><span><i class="core"></i>重点题材</span><em>气泡大小 = 用户占比 · 橙色虚线 = 占比加权均值</em></footer>
  </div>
</template>

<style scoped>
.chart-wrap{position:relative}.chart-canvas{width:100%;height:650px}.chart-state{height:650px;display:grid;justify-items:center;align-content:center;gap:9px}.chart-state b{font-size:13px}.chart-state span{color:var(--text-muted);font-size:9px}.chart-state.error b{color:var(--danger)}.chart-wrap footer{min-height:42px;display:flex;align-items:center;justify-content:center;gap:16px;border-top:1px solid var(--border-soft);color:var(--text-muted);font-size:9px}.chart-wrap footer span{display:flex;align-items:center;gap:5px}.chart-wrap footer i{width:8px;height:8px;border-radius:50%}.high{background:#60a5fa}.medium{background:#34d399}.low{background:#a78bfa}.chart-wrap footer .core{background:transparent;border:2px solid var(--accent)}.chart-wrap footer em{margin-left:14px;font-style:normal}
</style>
