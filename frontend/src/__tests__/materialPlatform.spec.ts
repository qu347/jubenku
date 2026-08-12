import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { defineComponent } from 'vue'
import { uploadMaterials } from '../api/materials'
import MaterialDetailDrawer from '../components/material/MaterialDetailDrawer.vue'
import MaterialCardGrid from '../components/material/MaterialCardGrid.vue'
import MaterialTable from '../components/material/MaterialTable.vue'
import MaterialFilterBar from '../components/material/MaterialFilterBar.vue'
import MaterialLibraryView from '../views/materials/MaterialLibraryView.vue'

const http = vi.hoisted(() => ({ request: vi.fn(), requestBlob: vi.fn() }))
const genreApi = vi.hoisted(() => ({ listGenreModules: vi.fn() }))
vi.mock('../api/http', () => http)
vi.mock('../api/genreModules', () => ({ ...genreApi, createGenreModule: vi.fn(), updateGenreModule: vi.fn(), deleteGenreModule: vi.fn(), duplicateGenreModule: vi.fn(), enableGenreModule: vi.fn(), disableGenreModule: vi.fn(), reorderGenreModules: vi.fn() }))

const material = {
  id: 'm1', library_type: 'material' as const, genre_module_id: 'g1', genre_module: { id: 'g1', name: '悬疑' }, title: '线索表', material_type: '剧情', description: '剧情摘要', tags: ['剧情:逆袭'], source: '',
  original_filename: '线索.txt', stored_filename: 'uuid.txt', storage_path: 'materials/uuid.txt', file_extension: 'txt', mime_type: 'text/plain', file_size: 12, has_attachment: true,
  created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z', deleted_at: null,
}

const ElTableStub = defineComponent({
  props: { data: { type: Array, default: () => [] } },
  provide() { return { testTableRows: this.data } },
  template: '<div><slot /></div>',
})
const ElTableColumnStub = defineComponent({
  inheritAttrs: false,
  inject: ['testTableRows'],
  template: '<div v-for="row in testTableRows" :key="row.id"><slot :row="row" /></div>',
})

const editDrawerStubs = {
  MaterialPreview: true,
  'el-drawer': { template: '<div><slot/><slot name="footer"/></div>' },
  'el-button': { template: '<button><slot /></button>' },
  'el-icon': true,
  'el-form': { template: '<form><slot /></form>' },
  'el-form-item': { template: '<label><slot /></label>' },
  'el-input': true,
  'el-select': {
    props: ['modelValue', 'placeholder'],
    emits: ['update:modelValue'],
    template: '<input v-if="placeholder === \'选择或输入上传平台\'" data-test="edit-platform" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /><select v-else :value="modelValue"><slot /></select>',
  },
  'el-option': true,
  'el-input-number': {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<input data-test="edit-heat" type="number" :value="modelValue ?? \'\'" @input="$emit(\'update:modelValue\', $event.target.value === \'\' ? null : Number($event.target.value))" />',
  },
  StandardTagSelector: true,
}

function mountEditableDetail(libraryType: 'material' | 'script' = 'material') {
  return mount(MaterialDetailDrawer, {
    props: {
      modelValue: true,
      initialMode: 'edit',
      libraryType,
      material: {
        ...material,
        library_type: libraryType,
        tags: ['剧情:逆袭', '时代背景:现代'],
        uploaded_by: '张三',
        project_owner: '李制片',
        upload_platform: libraryType === 'material' ? '番茄小说' : null,
        platform_heat: libraryType === 'material' ? 88 : null,
      },
      modules: [],
    },
    global: { stubs: editDrawerStubs },
  })
}

async function clickDetailSave(wrapper: ReturnType<typeof mountEditableDetail>) {
  await wrapper.findAll('button').find((button) => button.text() === '保存修改')!.trigger('click')
}

describe('素材平台 API', () => {
  beforeEach(() => { vi.clearAllMocks(); http.request.mockResolvedValue({}) })

  it('序列化自定义平台和热度', async () => {
    await uploadMaterials({ files: [new File(['x'], '素材.txt')], library_type: 'material', genre_module_id: 'g1', material_type: '剧情', tags: [], source: '', description: '摘要', upload_platform: '自定义平台', platform_heat: 88 })
    const postedFormData = http.request.mock.calls[0]?.[0].data as FormData
    expect(postedFormData.get('upload_platform')).toBe('自定义平台')
    expect(postedFormData.get('platform_heat')).toBe('88')
  })

  it('剧本上传不序列化素材平台字段', async () => {
    await uploadMaterials({ files: [new File(['x'], '剧本.txt')], library_type: 'script', genre_module_id: 'g1', material_type: '剧情', tags: [], source: '', description: '摘要' })
    const postedFormData = http.request.mock.calls[0]?.[0].data as FormData
    expect(postedFormData.has('upload_platform')).toBe(false)
    expect(postedFormData.has('platform_heat')).toBe(false)
  })
})

describe('素材平台展示', () => {
  it('详情和卡片展示平台信息，旧卡片提示待补充', () => {
    const detail = mount(MaterialDetailDrawer, {
      props: { modelValue: true, material: { ...material, upload_platform: '番茄小说', platform_heat: 88 }, modules: [] },
      global: { stubs: { MaterialPreview: true, 'el-drawer': { template: '<div><slot/><slot name="footer"/></div>' }, 'el-button': { template: '<button><slot /></button>' }, 'el-icon': true, 'el-form': true, 'el-form-item': true, 'el-input': true, 'el-select': true, 'el-option': true, 'el-input-number': true } },
    })
    expect(detail.text()).toContain('番茄小说')
    expect(detail.text()).toContain('88')
    const cards = mount(MaterialCardGrid, { props: { items: [{ ...material, upload_platform: null, platform_heat: null }] as never }, global: { stubs: { 'el-button': true, 'el-icon': true } } })
    expect(cards.text()).toContain('平台信息待补充')
  })

  it('素材编辑提供可自定义平台和限定范围的热度控件', async () => {
    const detail = mount(MaterialDetailDrawer, {
      props: { modelValue: true, initialMode: 'edit', material: { ...material, upload_platform: '番茄小说', platform_heat: 88 }, modules: [] },
      global: {
        stubs: {
          MaterialPreview: true,
          'el-drawer': { template: '<div><slot/><slot name="footer"/></div>' },
          'el-button': { template: '<button><slot /></button>' },
          'el-icon': true,
          'el-form': { template: '<form><slot /></form>' },
          'el-form-item': { template: '<label><slot /></label>' },
          'el-input': true,
          'el-select': { props: ['modelValue', 'allowCreate'], template: '<select data-test="edit-platform" :data-allow-create="allowCreate"><slot /></select>' },
          'el-option': true,
          'el-input-number': { props: ['modelValue', 'min', 'max', 'step'], template: '<input data-test="edit-heat" :min="min" :max="max" :step="step" />' },
          StandardTagSelector: true,
        },
      },
    })
    expect(detail.get('[data-test="edit-platform"]').attributes('data-allow-create')).toBeDefined()
    expect(detail.get('[data-test="edit-heat"]').attributes()).toMatchObject({ min: '0', max: '100', step: '1' })
  })

  it('素材编辑阻止仅填写热度', async () => {
    const detail = mountEditableDetail()

    await detail.get('[data-test="edit-platform"]').setValue('')
    await clickDetailSave(detail)
    expect(detail.emitted('save')).toBeUndefined()
  })

  it('素材编辑阻止仅填写平台', async () => {
    const detail = mountEditableDetail()

    await detail.get('[data-test="edit-heat"]').setValue('')
    await clickDetailSave(detail)
    expect(detail.emitted('save')).toBeUndefined()
  })

  it('素材编辑接受平台热度为 0，也允许同时清空平台信息', async () => {
    const detail = mountEditableDetail()

    await detail.get('[data-test="edit-heat"]').setValue('0')
    await clickDetailSave(detail)
    expect(detail.emitted('save')?.[0]?.[0]).toMatchObject({ upload_platform: '番茄小说', platform_heat: 0 })

    await detail.get('[data-test="edit-platform"]').setValue('')
    await detail.get('[data-test="edit-heat"]').setValue('')
    await clickDetailSave(detail)
    expect(detail.emitted('save')?.[1]?.[0]).toMatchObject({ upload_platform: null, platform_heat: null })
  })

  it('剧本编辑保存不发送素材平台字段', async () => {
    const detail = mountEditableDetail('script')
    await clickDetailSave(detail)
    const payload = detail.emitted('save')?.[0]?.[0] as Record<string, unknown>
    expect(payload).toBeDefined()
    expect(payload).not.toHaveProperty('upload_platform')
    expect(payload).not.toHaveProperty('platform_heat')
  })

  it('表格紧凑展示平台和热度，旧记录提示待补充', () => {
    const table = mount(MaterialTable, {
      props: {
        items: [
          { ...material, id: 'current', upload_platform: '番茄小说', platform_heat: 88 },
          { ...material, id: 'legacy', upload_platform: null, platform_heat: null },
        ] as never,
      },
      global: { stubs: { 'el-table': ElTableStub, 'el-table-column': ElTableColumnStub, 'el-button': true } },
    })
    expect(table.text()).toContain('番茄小说 · 热度 88')
    expect(table.text()).toContain('平台信息待补充')
  })
})

describe('素材平台筛选', () => {
  beforeEach(() => { setActivePinia(createPinia()); vi.clearAllMocks(); http.request.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20, pages: 0 }); genreApi.listGenreModules.mockResolvedValue([]) })

  it('筛选栏允许自定义平台，并在素材路由中保留 upload_platform', async () => {
    const filterOptions = { global: { stubs: { 'el-input': true, 'el-date-picker': true, 'el-option': true, 'el-select': { props: ['modelValue', 'allowCreate', 'filterable', 'defaultFirstOption'], template: '<select :data-allow-create="allowCreate"><slot /></select>' }, StandardTagSelector: true, 'el-button': { template: '<button><slot /></button>' } } } }
    const filter = mount(MaterialFilterBar, { props: { modelValue: {}, modules: [] }, ...filterOptions })
    expect(filter.get('[data-test="filter-platform"]').attributes('data-allow-create')).toBeDefined()
    const scriptFilter = mount(MaterialFilterBar, { props: { modelValue: {}, modules: [], libraryType: 'script' }, ...filterOptions })
    expect(scriptFilter.find('[data-test="filter-platform"]').exists()).toBe(false)

    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/materials', component: MaterialLibraryView }] })
    await router.push('/materials?upload_platform=番茄小说')
    await router.isReady()
    const view = shallowMount(MaterialLibraryView, { global: { plugins: [router], stubs: { 'el-select': true, 'el-option': true, 'el-pagination': true } } })
    await flushPromises()
    expect(http.request).toHaveBeenCalledWith(expect.objectContaining({ params: expect.objectContaining({ upload_platform: '番茄小说' }) }))
    view.findComponent(MaterialFilterBar).vm.$emit('apply', { upload_platform: '自定义平台', page: 1, page_size: 20, sort: 'created_desc' })
    await flushPromises()
    expect(router.currentRoute.value.query.upload_platform).toBe('自定义平台')
  })
})
