import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import MaterialUploadDrawer from '../components/material/MaterialUploadDrawer.vue'
import MaterialDetailDrawer from '../components/material/MaterialDetailDrawer.vue'
import MaterialPreview from '../components/material/MaterialPreview.vue'
import { useMaterialsStore } from '../stores/materials'

const api = vi.hoisted(() => ({ listMaterials: vi.fn(), uploadMaterials: vi.fn(), updateMaterial: vi.fn(), deleteMaterial: vi.fn(), downloadMaterial: vi.fn(), getMaterial: vi.fn() }))
const platformApi = vi.hoisted(() => ({ listUploadPlatforms: vi.fn(), createUploadPlatform: vi.fn() }))
vi.mock('../api/materials', () => api)
vi.mock('../api/uploadPlatforms', () => platformApi)

const material = {
  id: 'm1', genre_module_id: 'g1', genre_module: { id: 'g1', name: '悬疑' }, title: '线索表', material_type: '研究资料',
  description: '', tags: ['线索'], source: '内部', upload_platform: '番茄小说', platform_heat: 88, original_filename: '线索表.xlsx', stored_filename: 'uuid.xlsx',
  storage_path: 'materials/2026/08/uuid.xlsx', file_extension: 'xlsx', mime_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  file_size: 1024, has_attachment: true, created_at: '2026-08-11T00:00:00Z', updated_at: '2026-08-11T00:00:00Z', deleted_at: null,
}
const page = { items: [material], total: 1, page: 1, page_size: 20, pages: 1 }

describe('Sprint 3 素材 Store', () => {
  beforeEach(() => { setActivePinia(createPinia()); vi.clearAllMocks(); api.listMaterials.mockResolvedValue(page) })

  it('将题材、文件类型和关键词筛选参数正确发送', async () => {
    const store = useMaterialsStore()
    store.setFilters({ keyword: '线索', genre_module_id: 'g1', file_extension: 'xlsx', page: 1, page_size: 20 })
    await store.fetchMaterials()
    expect(api.listMaterials).toHaveBeenCalledWith(expect.objectContaining({ keyword: '线索', genre_module_id: 'g1', file_extension: 'xlsx' }))
    expect(store.items[0]?.id).toBe('m1')
  })

  it('多文件上传完成后刷新素材列表', async () => {
    api.uploadMaterials.mockResolvedValue({ success_count: 2, failure_count: 0, results: [], materials: [material] })
    const store = useMaterialsStore()
    await store.upload({ files: [new File(['a'], 'a.txt'), new File(['b'], 'b.md')], library_type: 'material', genre_module_id: 'g1', material_type: '研究资料', tags: [], source: '', description: '', upload_platform: '番茄小说', platform_heat: 88 })
    expect(api.uploadMaterials.mock.calls[0]?.[0].files).toHaveLength(2)
    expect(api.listMaterials).toHaveBeenCalledOnce()
  })

  it('编辑后立即替换当前表格记录', async () => {
    api.updateMaterial.mockResolvedValue({ ...material, title: '新版线索表' })
    const store = useMaterialsStore(); store.items = [material]
    await store.update('m1', { title: '新版线索表' })
    expect(store.items[0]?.title).toBe('新版线索表')
  })
})

describe('素材上传抽屉', () => {
  beforeEach(() => { setActivePinia(createPinia()); vi.clearAllMocks(); platformApi.listUploadPlatforms.mockResolvedValue([]); api.listMaterials.mockResolvedValue({ ...page, items: [], total: 0 }); api.uploadMaterials.mockResolvedValue({ success_count: 1, failure_count: 1, materials: [material], results: [{ filename: '成功.txt', success: true }, { filename: '失败.exe', success: false, error: '不允许的扩展名' }] }) })
  const stubs = {
    'el-drawer': { template: '<div><slot/><slot name="footer"/></div>', props: ['modelValue'] },
    'el-form': { template: '<form><slot/></form>' }, 'el-form-item': { template: '<label><slot/></label>' },
    'el-select': { props: ['modelValue'], emits: ['update:modelValue'], template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot/></select>' }, 'el-option': { template: '<option />' },
    'el-input': { props: ['modelValue'], emits: ['update:modelValue'], template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />' }, 'el-progress': { template: '<div class="progress-stub" />' },
    'el-input-number': { props: ['modelValue'], emits: ['update:modelValue'], template: '<input type="number" :value="modelValue" @input="$emit(\'update:modelValue\', Number($event.target.value))" />' },
  }

  it('选择多个文件后渲染待上传文件列表', async () => {
    const wrapper = mount(MaterialUploadDrawer, { props: { modelValue: true, modules: [{ id: 'g1', name: '悬疑' }] as never }, global: { stubs } })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['a'], 'A.txt'), new File(['b'], 'B.md')], configurable: true })
    await input.trigger('change')
    expect(wrapper.text()).toContain('A.txt')
    expect(wrapper.text()).toContain('B.md')
    expect(wrapper.text()).toContain('待上传 2 个')
  })

  it('部分失败时展示逐文件中文错误且仍刷新列表', async () => {
    const wrapper = mount(MaterialUploadDrawer, { props: { modelValue: true, modules: [{ id: 'g1', name: '悬疑' }] as never }, global: { stubs } })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['a'], '成功.txt'), new File(['b'], '失败.exe')], configurable: true })
    await input.trigger('change')
    await wrapper.get('[data-testid="story-summary-input"]').setValue('剧情摘要')
    await wrapper.get('[data-testid="uploaded-by-input"]').setValue('张三')
    await wrapper.get('[data-testid="project-owner-input"]').setValue('李制片')
    await wrapper.get('[data-test="upload-platform"]').setValue('番茄小说')
    await wrapper.get('[data-test="platform-heat"]').setValue(88)
    await wrapper.findAll('button').find((button) => button.text() === '逆袭')!.trigger('click')
    await wrapper.findAll('button').find((button) => button.text() === '现代')!.trigger('click')
    await wrapper.findAll('button').at(-1)?.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('不允许的扩展名')
    expect(api.listMaterials).toHaveBeenCalledOnce()
  })

  it('素材上传要求平台和热度，剧本上传不显示这些字段', async () => {
    const common = { props: { modelValue: true, modules: [{ id: 'g1', name: '悬疑' }] as never }, global: { stubs } }
    const wrapper = mount(MaterialUploadDrawer, common)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['a'], '素材.txt')], configurable: true })
    await input.trigger('change')
    await wrapper.get('[data-testid="story-summary-input"]').setValue('剧情摘要')
    await wrapper.get('[data-testid="uploaded-by-input"]').setValue('张三')
    await wrapper.get('[data-testid="project-owner-input"]').setValue('李制片')
    await wrapper.findAll('button').find((button) => button.text() === '逆袭')!.trigger('click')
    await wrapper.findAll('button').find((button) => button.text() === '现代')!.trigger('click')

    expect(wrapper.find('[data-test="add-custom-platform"]').exists()).toBe(true)
    await wrapper.get('[data-test="submit-upload"]').trigger('click')
    expect(wrapper.text()).toContain('请选择或输入上传平台')
    expect(wrapper.text()).toContain('请填写 0 到 100 的平台热度')

    const scriptWrapper = mount(MaterialUploadDrawer, { ...common, props: { ...common.props, libraryType: 'script' } })
    expect(scriptWrapper.find('[data-test="upload-platform"]').exists()).toBe(false)
    expect(scriptWrapper.find('[data-test="platform-heat"]').exists()).toBe(false)
  })
})

describe('素材预览', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('旧素材没有附件时不发起下载并给出明确说明', async () => {
    const wrapper = mount(MaterialPreview, {
      props: {
        material: {
          ...material,
          original_filename: '',
          stored_filename: '',
          storage_path: '',
          file_extension: '',
          mime_type: '',
          file_size: 0,
          has_attachment: false,
        } as never,
      },
      global: {
        stubs: {
          'el-icon': { template: '<i><slot /></i>' },
          'el-button': { template: '<button><slot /></button>' },
        },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('该素材没有附件')
    expect(wrapper.text()).toContain('升级前保留的素材记录')
    expect(api.downloadMaterial).not.toHaveBeenCalled()
  })

  it('兼容服务端带点扩展名并加载 TXT 内容', async () => {
    api.downloadMaterial.mockResolvedValue({ text: vi.fn().mockResolvedValue('真实文本预览内容') })
    const wrapper = mount(MaterialPreview, {
      props: {
        material: {
          ...material,
          original_filename: '对白.txt',
          file_extension: '.txt',
          mime_type: 'text/plain',
        } as never,
      },
      global: {
        stubs: {
          'el-icon': { template: '<i><slot /></i>' },
          'el-button': { template: '<button><slot /></button>' },
        },
      },
    })
    await flushPromises()
    expect(api.downloadMaterial).toHaveBeenCalledWith('m1')
    expect(wrapper.find('pre').text()).toContain('真实文本预览内容')
  })
})

describe('旧素材详情兼容', () => {
  it('无附件旧素材仍明确展示历史摘要和正文', () => {
    const wrapper = mount(MaterialDetailDrawer, {
      props: {
        modelValue: true,
        material: {
          ...material,
          description: '',
          legacy_summary: '旧素材中文摘要',
          legacy_content: '旧素材中文正文，升级后仍然可见。',
          original_filename: '',
          stored_filename: '',
          storage_path: '',
          file_extension: '',
          mime_type: '',
          file_size: 0,
          has_attachment: false,
        },
        modules: [],
      },
      global: {
        stubs: {
          MaterialPreview: { template: '<div>无附件预览</div>' },
          'el-drawer': { template: '<div><slot/><slot name="footer"/></div>' },
          'el-button': { template: '<button><slot /></button>' },
          'el-icon': { template: '<i><slot /></i>' },
          'el-form': { template: '<form><slot /></form>' },
          'el-form-item': { template: '<label><slot /></label>' },
          'el-input': { template: '<input />' },
          'el-select': { template: '<select><slot /></select>' },
          'el-option': { template: '<option />' }, 'el-input-number': true,
        },
      },
    })
    expect(wrapper.text()).toContain('旧素材中文摘要')
    expect(wrapper.text()).toContain('剧情正文')
    expect(wrapper.text()).toContain('升级后仍然可见')
  })

  it('Markdown 正文未随列表返回时只显示文件预览，不叠加不可预览提示', () => {
    const wrapper = mount(MaterialDetailDrawer, {
      props: {
        modelValue: true,
        material: { ...material, file_extension: 'md', original_filename: '剧情.md', content_text: '', legacy_content: '' },
        modules: [],
      },
      global: {
        stubs: {
          MaterialPreview: { template: '<div>Markdown 文件正文</div>' },
          'el-drawer': { template: '<div><slot/><slot name="footer"/></div>' },
          'el-button': { template: '<button><slot /></button>' },
          'el-icon': { template: '<i><slot /></i>' },
          'el-form': { template: '<form><slot /></form>' },
          'el-form-item': { template: '<label><slot /></label>' },
          'el-input': { template: '<input />' },
          'el-select': { template: '<select><slot /></select>' },
          'el-option': { template: '<option />' }, 'el-input-number': true,
        },
      },
    })
    expect(wrapper.text()).toContain('Markdown 文件正文')
    expect(wrapper.text()).not.toContain('当前格式暂不支持直接阅读')
  })
})
