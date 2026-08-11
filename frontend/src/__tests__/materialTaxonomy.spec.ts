import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StandardTagSelector from '../components/material/StandardTagSelector.vue'
import { decodeStandardTags, encodeStandardTags } from '../utils/materialTaxonomy'

describe('剧情素材标准标签', () => {
  it('按照剧情、情绪、时代背景和角色设定保存分组标签', () => {
    const tags = encodeStandardTags({ plot: ['逆袭'], emotion: ['紧张'], era: ['架空'], role: ['小人物'] })
    expect(tags).toEqual(['剧情:逆袭', '情绪:紧张', '时代背景:架空', '角色设定:小人物'])
    expect(decodeStandardTags(tags).selections.era).toEqual(['架空'])
  })

  it('时代背景保持单选，剧情允许多选', async () => {
    const wrapper = mount(StandardTagSelector, { props: { modelValue: [] } })
    await wrapper.findAll('button').find((button) => button.text() === '现代')!.trigger('click')
    await wrapper.setProps({ modelValue: wrapper.emitted('update:modelValue')!.at(-1)![0] as string[] })
    await wrapper.findAll('button').find((button) => button.text() === '古代')!.trigger('click')
    const eraTags = (wrapper.emitted('update:modelValue')!.at(-1)![0] as string[]).filter((tag) => tag.startsWith('时代背景:'))
    expect(eraTags).toEqual(['时代背景:古代'])
  })

  it('支持用逗号添加和删除自定义标签', async () => {
    const wrapper = mount(StandardTagSelector, { props: { modelValue: [] } })
    const input = wrapper.get('.custom-input input')
    await input.setValue('冷幽默,非线性叙事')
    await input.trigger('keydown', { key: 'Enter' })
    const added = wrapper.emitted('update:modelValue')!.at(-1)![0] as string[]
    expect(added).toEqual(['冷幽默', '非线性叙事'])

    await wrapper.setProps({ modelValue: added })
    await wrapper.get('button[aria-label="删除自定义标签 冷幽默"]').trigger('click')
    expect(wrapper.emitted('update:modelValue')!.at(-1)![0]).toEqual(['非线性叙事'])
  })
})
