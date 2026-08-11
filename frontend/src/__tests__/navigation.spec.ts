import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import AppLayout from '../components/module/AppLayout.vue'

const apiMocks = vi.hoisted(() => ({ listGenreModules: vi.fn() }))
vi.mock('../api/genreModules', () => ({
  ...apiMocks,
  createGenreModule: vi.fn(), updateGenreModule: vi.fn(), deleteGenreModule: vi.fn(),
  duplicateGenreModule: vi.fn(), enableGenreModule: vi.fn(), disableGenreModule: vi.fn(), reorderGenreModules: vi.fn(),
}))

const moduleItem = {
  id: '1', name: '规则怪谈', slug: 'rule-horror', icon: 'Collection', description: '',
  theme_color: '#FF7A45', sort_order: 0, status: 'active', visible: true, profile_json: {},
  created_at: '2026-08-11', updated_at: '2026-08-11', deleted_at: null, material_count: 0, section_count: 1,
}

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/genres/:slug', name: 'genre-module', component: { template: '<div />' } },
      { path: '/settings/modules', component: { template: '<div />' } },
      { path: '/materials', component: { template: '<div />' } },
      { path: '/genre-map', component: { template: '<div />' } },
    ],
  })
}

describe('动态题材导航', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    apiMocks.listGenreModules.mockResolvedValue([moduleItem])
  })

  it('根据真实接口结果渲染题材菜单', async () => {
    const router = createTestRouter()
    await router.push('/')
    await router.isReady()
    const wrapper = mount(AppLayout, { global: { plugins: [router], stubs: { RouterView: true } } })
    await flushPromises()
    expect(wrapper.text()).toContain('规则怪谈')
    expect(wrapper.find('a[href="/genres/rule-horror"]').exists()).toBe(true)
  })

  it('点击题材进入正确 slug 路由', async () => {
    const router = createTestRouter()
    await router.push('/')
    await router.isReady()
    const wrapper = mount(AppLayout, { global: { plugins: [router], stubs: { RouterView: true } } })
    await flushPromises()
    await wrapper.find('a[href="/genres/rule-horror"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe('/genres/rule-horror')
  })
})
