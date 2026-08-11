import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import GenreMetricImportDialog from '../components/genre-map/GenreMetricImportDialog.vue'

const api=vi.hoisted(()=>({importGenreMetrics:vi.fn()}))
vi.mock('../api/genreMetrics',()=>({...api,listGenreMetrics:vi.fn(),getGenreMetric:vi.fn(),createGenreMetric:vi.fn(),updateGenreMetric:vi.fn(),deleteGenreMetric:vi.fn(),downloadGenreMetricTemplate:vi.fn(),exportGenreMetrics:vi.fn()}))

describe('定位数据导入结果',()=>{
  beforeEach(()=>{vi.clearAllMocks();api.importGenreMetrics.mockResolvedValue({success_count:2,failure_count:1,errors:[{row:4,field:'题材',reason:'题材名称不存在'}]})})
  it('Excel 部分错误时展示失败行、字段和中文原因',async()=>{const wrapper=mount(GenreMetricImportDialog,{props:{modelValue:true},global:{stubs:{'el-dialog':{template:'<div><slot/><slot name="footer"/></div>'}}}});const input=wrapper.find('input[type="file"]');Object.defineProperty(input.element,'files',{value:[new File(['xlsx'],'定位数据.xlsx')],configurable:true});await input.trigger('change');await wrapper.findAll('button').at(-1)?.trigger('click');await flushPromises();expect(wrapper.text()).toContain('第 4 行');expect(wrapper.text()).toContain('题材名称不存在');expect(wrapper.emitted('complete')).toHaveLength(1)})
})
