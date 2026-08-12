import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useGenreModulesStore } from '../stores/genreModules'

const apiMocks = vi.hoisted(() => ({
  listGenreModules: vi.fn(),
  createGenreModule: vi.fn(),
  updateGenreModule: vi.fn(),
  deleteGenreModule: vi.fn(),
  duplicateGenreModule: vi.fn(),
  enableGenreModule: vi.fn(),
  disableGenreModule: vi.fn(),
  reorderGenreModules: vi.fn(),
}))

vi.mock('../api/genreModules', () => apiMocks)

const sampleModule = {
  id: '1', name: '规则怪谈', slug: 'rule-horror', icon: 'Collection', description: '',
  theme_color: '#FF7A45', sort_order: 0, status: 'active' as const, visible: true,
  profile_json: {}, created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z',
  deleted_at: null, material_count: 0, section_count: 9,
}

describe('GenreModule Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('能成功读取题材导航列表', async () => {
    apiMocks.listGenreModules
      .mockResolvedValueOnce([sampleModule])
      .mockResolvedValueOnce([{ ...sampleModule, id: '2', name: '都市日常', slug: 'urban-daily' }])
    const store = useGenreModulesStore()
    await store.fetchNavigationModules()
    expect(apiMocks.listGenreModules).toHaveBeenNthCalledWith(1, { library_type: 'material' })
    expect(apiMocks.listGenreModules).toHaveBeenNthCalledWith(2, { library_type: 'script' })
    expect(store.materialModules).toEqual([sampleModule])
    expect(store.scriptModules[0]?.slug).toBe('urban-daily')
    expect(store.error).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('接口失败时保存错误状态', async () => {
    apiMocks.listGenreModules.mockRejectedValue(new Error('服务不可用'))
    const store = useGenreModulesStore()
    await store.fetchNavigationModules()
    expect(store.materialModules).toEqual([])
    expect(store.scriptModules).toEqual([])
    expect(store.error).toBe('服务不可用')
  })

  it('停用模块后刷新普通导航', async () => {
    apiMocks.disableGenreModule.mockResolvedValue({ ...sampleModule, status: 'inactive' })
    apiMocks.listGenreModules
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([{ ...sampleModule, status: 'inactive' }])
    const store = useGenreModulesStore()
    await store.disableModule(sampleModule.id)
    expect(apiMocks.disableGenreModule).toHaveBeenCalledWith(sampleModule.id)
    expect(store.materialModules).toEqual([])
  })
})
