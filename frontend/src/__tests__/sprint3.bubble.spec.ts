import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import GenreBubbleChart from '../components/genre-map/GenreBubbleChart.vue'
import GenreMetricDetailDrawer from '../components/genre-map/GenreMetricDetailDrawer.vue'
import type { GenreMetric } from '../types/genreMetric'

const chart = vi.hoisted(() => ({ setOption: vi.fn(), resize: vi.fn(), dispose: vi.fn(), handler: undefined as ((params: unknown) => void) | undefined }))
vi.mock('echarts', () => ({
  init: () => ({
    setOption: chart.setOption,
    resize: chart.resize,
    dispose: chart.dispose,
    on: (_event: string, handler: (params: unknown) => void) => { chart.handler = handler },
  }),
}))

const metric: GenreMetric = { id: 'x1', genre_module_id: 'g1', genre_module: { id: 'g1', name: '悬疑', slug: 'suspense' }, platform: '番茄小说', channel: '男频', period: '2026-08', average_age: 24, age_group: 'middle', education_level: 'medium', audience_share: 25, heat_index: 88, trend: 'rising', is_core: true, sample_size: 2000, data_source: '调研', remark: '', created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z', deleted_at: null }

describe('题材气泡图交互', () => {
  beforeAll(() => {
    globalThis.ResizeObserver = class { observe() {} disconnect() {} unobserve() {} }
    Object.defineProperty(HTMLElement.prototype, 'clientWidth', { value: 1000, configurable: true })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', { value: 650, configurable: true })
  })
  beforeEach(() => { vi.clearAllMocks(); chart.handler = undefined })

  it('按年龄、学历与用户占比生成气泡数据', async () => {
    mount(GenreBubbleChart, { props: { items: [metric] } })
    await flushPromises()
    const option = chart.setOption.mock.calls.at(-1)?.[0] as { series: Array<{ data: Array<{ value: number[]; symbolSize: number }> }> }
    expect(option.series[0]?.data[0]?.value).toEqual([24, 2, 25])
    expect(option.series[0]?.data[0]?.symbolSize).toBeGreaterThan(20)
  })

  it('tooltip 使用非 HTML 渲染，数据库文本不会作为 DOM 注入', async () => {
    mount(GenreBubbleChart, { props: { items: [{ ...metric, platform: '<img src=x onerror=alert(1)>' }] } })
    await flushPromises()
    const option = chart.setOption.mock.calls.at(-1)?.[0] as { tooltip: { renderMode: string; formatter: (params: unknown) => string } }
    expect(option.tooltip.renderMode).toBe('richText')
    expect(option.tooltip.formatter({ data: { raw: metric } })).not.toContain('<br>')
  })

  it('点击气泡打开该条定位数据详情', async () => {
    const wrapper = mount(GenreBubbleChart, { props: { items: [metric] } })
    await flushPromises()
    chart.handler?.({ data: { raw: metric } })
    expect(wrapper.emitted('select')?.[0]).toEqual([metric])
  })

  it('详情中的查看素材操作携带当前题材记录', async () => {
    const wrapper = mount(GenreMetricDetailDrawer, { props: { modelValue: true, metric }, global: { stubs: { 'el-drawer': { template: '<div><slot/><slot name="footer"/></div>' } } } })
    await wrapper.findAll('button').at(-1)?.trigger('click')
    expect(wrapper.emitted('materials')?.[0]).toEqual([metric])
  })
})
