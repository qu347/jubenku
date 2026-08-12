import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { flushPromises, shallowMount } from '@vue/test-utils'
import { buildGenreHeatTrendOption } from '../utils/genreHeatTrend'
import GenreMapView from '../views/GenreMapView.vue'
import GenrePositioningTable from '../components/genre-map/GenrePositioningTable.vue'
import { useGenrePositioningStore } from '../stores/genrePositioning'
import type { GenrePositioningTimeline } from '../types/genrePositioning'

const api = vi.hoisted(() => ({ listGenrePositioning: vi.fn(), getGenrePositioningTimeline: vi.fn() }))
const platformApi = vi.hoisted(() => ({ listUploadPlatforms: vi.fn(), createUploadPlatform: vi.fn() }))
vi.mock('../api/genrePositioning', () => api)
vi.mock('../api/uploadPlatforms', () => platformApi)

const timeline: GenrePositioningTimeline = {
  upload_platform: '抖音',
  periods: ['2026-06', '2026-07', '2026-08'],
  points: [
    { genre_module_id: 'g1', genre_name: '西方奇幻', theme_color: '#8b5cf6', period: '2026-06', average_heat: 80, material_count: 2 },
    { genre_module_id: 'g1', genre_name: '西方奇幻', theme_color: '#8b5cf6', period: '2026-08', average_heat: 90, material_count: 1 },
    { genre_module_id: 'g2', genre_name: '悬疑灵异', theme_color: '#06b6d4', period: '2026-07', average_heat: 72, material_count: 3 },
  ],
  total_materials: 6,
}

function listResult() {
  return {
    items: [
      { genre_module_id: 'g1', genre_name: '西方奇幻', theme_color: '#8b5cf6', upload_platform: '抖音', average_heat: 85, material_count: 3, latest_updated_at: '2026-08-12T00:00:00Z' },
      { genre_module_id: 'g2', genre_name: '悬疑灵异', theme_color: '#06b6d4', upload_platform: ' 抖音 ', average_heat: 72, material_count: 3, latest_updated_at: '2026-08-12T00:00:00Z' },
      { genre_module_id: 'g3', genre_name: '都市日常', theme_color: '#22c55e', upload_platform: '自定义平台', average_heat: 66, material_count: 1, latest_updated_at: '2026-08-12T00:00:00Z' },
    ],
    total: 3,
  }
}

describe('题材平台月度热度趋势', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.setItem('genre-map-view', 'chart')
    vi.clearAllMocks()
    api.listGenrePositioning.mockResolvedValue(listResult())
    api.getGenrePositioningTimeline.mockImplementation(async (platform?: string) => ({ ...timeline, upload_platform: platform || '全部平台' }))
    platformApi.listUploadPlatforms.mockResolvedValue([
      { id: 'p1', name: '抖音', is_system: true },
      { id: 'p2', name: '星河阅读', is_system: false },
    ])
  })

  it('从有效素材汇总平台并自动包含自定义平台', async () => {
    const store = useGenrePositioningStore()
    await store.fetchPlatforms('自定义平台')
    expect(store.platforms[0]).toBe('全部平台')
    expect(store.platforms).toEqual(expect.arrayContaining(['抖音', '自定义平台', '星河阅读']))
    expect(new Set(store.platforms).size).toBe(store.platforms.length)
    expect(store.selectedPlatform).toBe('自定义平台')
    expect(api.getGenrePositioningTimeline).toHaveBeenCalledWith('自定义平台')
  })

  it('默认选择全部平台并请求跨平台题材趋势', async () => {
    const store = useGenrePositioningStore()

    await store.fetchPlatforms()

    expect(store.platforms[0]).toBe('全部平台')
    expect(store.selectedPlatform).toBe('全部平台')
    expect(api.getGenrePositioningTimeline).toHaveBeenCalledWith(undefined)
  })

  it('没有素材数据的已保存平台也会出现在定位图选择器', async () => {
    const store = useGenrePositioningStore()

    await store.fetchPlatforms()

    expect(store.platforms).toContain('星河阅读')
    await store.selectPlatform('星河阅读')
    expect(api.getGenrePositioningTimeline).toHaveBeenCalledWith('星河阅读')
  })

  it('生成每个题材一条平滑曲线，缺失月份为空且热度轴固定为0到100', () => {
    const option = buildGenreHeatTrendOption(timeline) as {
      xAxis: { data: string[] }
      yAxis: { min: number; max: number }
      tooltip: { renderMode: string; formatter: (params: unknown) => string }
      series: Array<{ name: string; type: string; smooth: boolean; connectNulls: boolean; data: Array<{ value: number } | null> }>
    }
    expect(option.xAxis.data).toEqual(timeline.periods)
    expect(option.yAxis).toMatchObject({ min: 0, max: 100 })
    expect(option.series.map((item) => item.name)).toEqual(['西方奇幻', '悬疑灵异'])
    expect(option.series[0]).toMatchObject({ type: 'line', smooth: true, connectNulls: false })
    expect(option.series[0]?.data.map((item) => item?.value ?? null)).toEqual([80, null, 90])
    expect(option.tooltip.renderMode).toBe('richText')
    const tooltip = option.tooltip.formatter({ data: { value: 80, raw: timeline.points[0] } })
    expect(tooltip).toContain('平台：抖音')
    expect(tooltip).not.toContain('<br>')
  })

  it('月份超过12个时启用横向缩放', () => {
    const periods = Array.from({ length: 13 }, (_, index) => `2025-${String(index + 1).padStart(2, '0')}`)
    const option = buildGenreHeatTrendOption({ ...timeline, periods }) as { dataZoom: unknown[] }
    expect(option.dataZoom).toHaveLength(2)
  })

  it('页面选择平台并从月度数据点进入对应素材列表', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/genre-map', component: GenreMapView },
        { path: '/materials', component: { template: '<div />' } },
      ],
    })
    await router.push('/genre-map?upload_platform=抖音')
    await router.isReady()
    const wrapper = shallowMount(GenreMapView, { global: { plugins: [router], stubs: { 'el-select': true, 'el-option': true } } })
    await flushPromises()
    expect(wrapper.text()).toContain('题材平台热度趋势图')
    expect(wrapper.text()).not.toContain('平均年龄')
    await wrapper.findAll('.view-switch button')[1]?.trigger('click')
    wrapper.findComponent(GenrePositioningTable).vm.$emit('view', timeline.points[0])
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/materials')
    expect(router.currentRoute.value.query).toMatchObject({ genre_module_id: 'g1', upload_platform: '抖音' })
  })
})
