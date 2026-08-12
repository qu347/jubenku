import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia } from 'pinia'
import GenreModuleView from '../views/GenreModuleView.vue'
import { ApiError } from '../api/http'

const apiMocks = vi.hoisted(() => ({
  getGenreModuleBySlug: vi.fn(),
  listGenreModules: vi.fn(),
  listMaterials: vi.fn(),
  getMaterial: vi.fn(),
  updateMaterial: vi.fn(),
  deleteMaterial: vi.fn(),
  downloadMaterial: vi.fn(),
  listGenreMetrics: vi.fn(),
}))
vi.mock('../api/genreModules', () => ({
  getGenreModuleBySlug: apiMocks.getGenreModuleBySlug,
  listGenreModules: apiMocks.listGenreModules,
}))
vi.mock('../api/materials', () => ({
  listMaterials: apiMocks.listMaterials,
  getMaterial: apiMocks.getMaterial,
  updateMaterial: apiMocks.updateMaterial,
  deleteMaterial: apiMocks.deleteMaterial,
  downloadMaterial: apiMocks.downloadMaterial,
  uploadMaterials: vi.fn(),
}))
vi.mock('../api/genreMetrics', () => ({ listGenreMetrics: apiMocks.listGenreMetrics }))

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
      { path: '/script-genres/:slug', name: 'script-genre-module', component: GenreModuleView },
      { path: '/settings/modules', component: { template: '<div />' } },
      { path: '/materials', component: { template: '<div />' } },
      { path: '/genre-map', component: { template: '<div />' } },
    ],
  })
}

function material(id: string, title: string, materialType: string) {
  return {
    id, genre_module_id: 'western-fantasy', genre_module: { id: 'western-fantasy', name: '西方奇幻' },
    title, material_type: materialType, description: '案例说明', legacy_summary: '', legacy_content: '',
    tags: ['案例'], source: '原创', original_filename: `${title}.md`, stored_filename: `${id}.md`,
    storage_path: `2026/08/${id}.md`, file_extension: '.md', mime_type: 'text/markdown', file_size: 100,
    has_attachment: true, created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z', deleted_at: null,
  }
}

describe('题材详情页', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiMocks.listGenreModules.mockResolvedValue([])
    apiMocks.listMaterials.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100, pages: 0 })
    apiMocks.listGenreMetrics.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100, pages: 0 })
  })

  it('能够根据路由切换模块', async () => {
    apiMocks.getGenreModuleBySlug.mockImplementation((slug: string) => Promise.resolve(detail(slug, slug === 'rule-horror' ? '规则怪谈' : '东方仙侠')))
    const router = testRouter()
    await router.push('/genres/rule-horror')
    await router.isReady()
    const wrapper = mount(GenreModuleView, { global: { plugins: [router, createPinia()] } })
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
    const wrapper = mount(GenreModuleView, { global: { plugins: [router, createPinia()] } })
    await flushPromises()
    expect(wrapper.text()).toContain('404')
    expect(wrapper.text()).toContain('题材不存在')
  })

  it('只保留标题模块并显示标准列表字段和全部题材素材', async () => {
    const moduleDetail = detail('western-fantasy', '西方奇幻')
    moduleDetail.sections.push({
      ...moduleDetail.sections[0]!, id: 'characters-section', section_key: 'characters', section_name: '人物素材', sort_order: 1,
    })
    apiMocks.getGenreModuleBySlug.mockResolvedValue(moduleDetail)
    apiMocks.listMaterials.mockResolvedValue({
      items: [material('character-1', '灰塔守钟人', '人物素材'), material('reference-1', '魔法史研究', '研究资料')],
      total: 2, page: 1, page_size: 100, pages: 1,
    })
    const router = testRouter()
    await router.push('/genres/western-fantasy')
    await router.isReady()
    const wrapper = mount(GenreModuleView, { global: { plugins: [router, createPinia()] } })
    await flushPromises()

    expect(wrapper.text()).toContain('ONLY MODULE')
    expect(wrapper.text()).toContain('标题')
    expect(wrapper.text()).toContain('摘要')
    expect(wrapper.text()).toContain('上传人')
    expect(wrapper.text()).toContain('对接项目负责人')
    expect(wrapper.text()).toContain('时间')
    expect(wrapper.text()).toContain('灰塔守钟人')
    expect(wrapper.text()).toContain('魔法史研究')
    expect(wrapper.get('.story-table caption').text()).toBe('西方奇幻剧情列表')
    expect(wrapper.find('.section-tabs').exists()).toBe(false)
  })

  it('在当前题材标题列表上方按标准标签筛选', async () => {
    apiMocks.getGenreModuleBySlug.mockResolvedValue(detail('western-fantasy', '西方奇幻'))
    const router = testRouter()
    await router.push('/genres/western-fantasy')
    await router.isReady()
    const wrapper = mount(GenreModuleView, { global: { plugins: [router, createPinia()] } })
    await flushPromises()

    expect(wrapper.text()).toContain('标准素材标签')
    expect(wrapper.text()).not.toContain('全部题材')
    await wrapper.findAll('button').find((button) => button.text() === '逆袭')!.trigger('click')
    await wrapper.findAll('button').find((button) => button.text() === '应用筛选')!.trigger('click')
    await flushPromises()
    expect(apiMocks.listMaterials).toHaveBeenLastCalledWith(expect.objectContaining({
      library_type: 'material',
      genre_module_id: 'western-fantasy',
      tags: '剧情:逆袭',
      page: 1,
      page_size: 100,
    }))
  })

  it('剧本题材页只请求剧本并显示添加剧本', async () => {
    apiMocks.getGenreModuleBySlug.mockResolvedValue(detail('western-fantasy', '西方奇幻'))
    const router = testRouter()
    await router.push('/script-genres/western-fantasy')
    await router.isReady()
    const wrapper = mount(GenreModuleView, {
      props: { libraryType: 'script' },
      global: { plugins: [router, createPinia()] },
    })
    await flushPromises()

    expect(apiMocks.listMaterials).toHaveBeenCalledWith(expect.objectContaining({
      genre_module_id: 'western-fantasy',
      library_type: 'script',
    }))
    expect(wrapper.text()).toContain('添加剧本')
    expect(wrapper.text()).toContain('剧本标题')
  })
})
