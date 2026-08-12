import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ModuleSettingsView from '../views/settings/ModuleSettingsView.vue'

const api = vi.hoisted(() => ({
  listGenreModules: vi.fn(), createGenreModule: vi.fn(), updateGenreModule: vi.fn(),
  deleteGenreModule: vi.fn(), duplicateGenreModule: vi.fn(), enableGenreModule: vi.fn(),
  disableGenreModule: vi.fn(), reorderGenreModules: vi.fn(),
}))
vi.mock('../api/genreModules', () => api)

const moduleItem = {
  id: 'genre-id', name: '西方奇幻', slug: 'western-fantasy', icon: 'Collection',
  description: '', theme_color: '#8B5CF6', sort_order: 0, status: 'active', visible: true,
  material_visible: true, script_visible: true, material_sort_order: 0, script_sort_order: 0,
  profile_json: {}, created_at: '2026-08-12', updated_at: '2026-08-12', deleted_at: null,
  material_count: 4, script_count: 2, section_count: 1,
}

describe('题材配置双栏', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    api.listGenreModules.mockResolvedValue([moduleItem])
    api.updateGenreModule.mockResolvedValue(moduleItem)
  })

  it('同时显示素材题材配置和剧本题材配置', async () => {
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
    await wrapper.find('[data-testid="script-genre-config"] el-switch').trigger('change')
    await flushPromises()
    expect(api.updateGenreModule).toHaveBeenCalledWith('genre-id', { script_visible: false })
  })

  it('将题材删除明确标记为不可恢复的永久删除', async () => {
    const wrapper = mount(ModuleSettingsView, {
      global: {
        stubs: {
          'el-dropdown': { template: '<div><slot /><slot name="dropdown" /></div>' },
          'el-dropdown-menu': { template: '<div><slot /></div>' },
          'el-dropdown-item': { template: '<button><slot /></button>' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('永久删除')
    expect(wrapper.text()).not.toContain('软删除')
  })
})
