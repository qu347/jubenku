import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LegacyMaterialTable from '../components/MaterialTable.vue'

describe('原生数据表格可访问性', () => {
  it('素材表格提供可被辅助技术读取的标题', () => {
    const wrapper = mount(LegacyMaterialTable, { props: { materials: [] } })

    expect(wrapper.get('table caption').text()).toBe('素材列表')
  })
})
