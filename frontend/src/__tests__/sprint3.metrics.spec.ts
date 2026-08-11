import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useGenreMetricsStore } from '../stores/genreMetrics'
import { bubbleSize, EDUCATION_SCORE, regionShare, weightedMean } from '../utils/genreMap'
import type { GenreMetric } from '../types/genreMetric'

const api = vi.hoisted(() => ({ listGenreMetrics: vi.fn(), createGenreMetric: vi.fn(), updateGenreMetric: vi.fn(), deleteGenreMetric: vi.fn(), getGenreMetric: vi.fn(), importGenreMetrics: vi.fn(), downloadGenreMetricTemplate: vi.fn(), exportGenreMetrics: vi.fn() }))
vi.mock('../api/genreMetrics', () => api)

const metric: GenreMetric = { id: 'x1', genre_module_id: 'g1', genre_module: { id: 'g1', name: '悬疑' }, platform: '番茄小说', channel: '男频', period: '2026-08', average_age: 24, age_group: 'middle', education_level: 'medium', audience_share: 25, heat_index: 88, trend: 'rising', is_core: true, sample_size: 2000, data_source: '调研', remark: '', created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z', deleted_at: null }

describe('Sprint 3 定位数据 Store', () => {
  beforeEach(() => { setActivePinia(createPinia()); vi.clearAllMocks(); api.listGenreMetrics.mockResolvedValue({ items: [metric], total: 1, page: 1, page_size: 100, pages: 1 }) })
  it('发送平台和学历筛选并保存响应', async () => { const store=useGenreMetricsStore();store.setFilters({platform:'番茄小说',education_level:'medium'});await store.fetchMetrics();expect(api.listGenreMetrics).toHaveBeenCalledWith(expect.objectContaining({platform:'番茄小说',education_level:'medium'}));expect(store.total).toBe(1) })
  it('新增后立即刷新图表数据', async () => { api.createGenreMetric.mockResolvedValue(metric);const store=useGenreMetricsStore();await store.create({genre_module_id:'g1',platform:'番茄小说',channel:'男频',period:'2026-08',average_age:24,age_group:'middle',education_level:'medium',audience_share:25,heat_index:88,trend:'rising',is_core:true,sample_size:2000,data_source:'调研',remark:''});expect(api.listGenreMetrics).toHaveBeenCalledOnce() })
  it('修改与删除后都重新获取定位数据', async () => { api.updateGenreMetric.mockResolvedValue({...metric,average_age:30});api.deleteGenreMetric.mockResolvedValue({id:'x1'});const store=useGenreMetricsStore();await store.update('x1',{average_age:30});await store.remove('x1');expect(api.listGenreMetrics).toHaveBeenCalledTimes(2) })
  it('定位数据超过100条时获取全部分页，避免图表静默遗漏', async () => { api.listGenreMetrics.mockResolvedValueOnce({items:[metric],total:101,page:1,page_size:100,pages:2}).mockResolvedValueOnce({items:[{...metric,id:'x2'}],total:101,page:2,page_size:100,pages:2});const store=useGenreMetricsStore();await store.fetchMetrics();expect(api.listGenreMetrics).toHaveBeenNthCalledWith(2,expect.objectContaining({page:2,page_size:100}));expect(store.items.map(item=>item.id)).toEqual(['x1','x2']);expect(store.total).toBe(101) })
})

describe('气泡映射算法', () => {
  it('坐标由年龄和学历映射，大小随用户占比增加', () => { expect([metric.average_age, EDUCATION_SCORE[metric.education_level]]).toEqual([24,2]);expect(bubbleSize(36)).toBeGreaterThan(bubbleSize(9)) })
  it('平均线优先按用户占比加权', () => { const second={...metric,id:'x2',average_age:44,audience_share:75};expect(weightedMean([metric,second],item=>item.average_age)).toBe(39) })
  it('占比全部为零时回退普通平均值', () => { const a={...metric,audience_share:0,average_age:20};const b={...metric,id:'x2',audience_share:0,average_age:40};expect(weightedMean([a,b],item=>item.average_age)).toBe(30) })
  it('九宫格显示每个区域用户占比合计', () => { const second={...metric,id:'x2',audience_share:15};expect(regionShare([metric,second],'middle','medium')).toBe(40) })
})
