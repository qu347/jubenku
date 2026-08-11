import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import GenreModuleView from '../views/GenreModuleView.vue'
import { ApiError } from '../api/http'

const apiMocks = vi.hoisted(() => ({ getGenreModuleBySlug: vi.fn() }))
vi.mock('../api/genreModules', () => ({ getGenreModuleBySlug: apiMocks.getGenreModuleBySlug }))

function detail(slug: string, name: string) {
  return {
    id: slug, name, slug, icon: 'Collection', description: `${name}简介`, theme_color: '#FF7A45',
    sort_order: 0, status: 'active', visible: true, profile_json: {}, created_at: '2026-08-11',
    updated_at: '2026-08-11', deleted_at: null, material_count: 0, section_count: 1,
    sections: [{
      id: `${slug}-section`, genre_module_id: slug, section_key: 'overview', section_name: '概览',
      icon: 'Collection', sort_order: 0, enabled: true, field_schema: [], filter_schema: {}, card_schema: {},
      created_at: '2026-08-11', updated_at: '2026-08-11', deleted_at: null, material_count: 0,
    }],
  }
}

function testRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/genres/:slug', name: 'genre-module', component: GenreModuleView },
      { path: '/settings/modules', component: { template: '<div />' } },
    ],
  })
}

describe('题材详情页', () => {
  beforeEach(() => vi.clearAllMocks())

  it('能够根据路由切换模块', async () => {
    apiMocks.getGenreModuleBySlug.mockImplementation((slug: string) => Promise.resolve(detail(slug, slug === 'rule-horror' ? '规则怪谈' : '东方仙侠')))
    const router = testRouter()
    await router.push('/genres/rule-horror')
    await router.isReady()
    const wrapper = mount(GenreModuleView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.text()).toContain('规则怪谈')
    await router.push('/genres/eastern-xianxia')
    await flushPromises()
    expect(wrapper.text()).toContain('东方仙侠')
    expect(apiMocks.getGenreModuleBySlug).toHaveBeenLastCalledWith('eastern-xianxia')
  })

  it('不存在 slug 时显示 404', async () => {
    apiMocks.getGenreModuleBySlug.mockRejectedValue(new ApiError('题材模块不存在', 404, 'genre_not_found'))
    const router = testRouter()
    await router.push('/genres/missing')
    await router.isReady()
    const wrapper = mount(GenreModuleView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.text()).toContain('404')
    expect(wrapper.text()).toContain('题材不存在')
  })
})
