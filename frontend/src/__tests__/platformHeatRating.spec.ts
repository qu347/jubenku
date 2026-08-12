import { describe, expect, it } from 'vitest'
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import PlatformHeatInput from '../components/material/PlatformHeatInput.vue'
import { getPlatformHeatRating } from '../utils/platformHeatRating'


const InputNumberStub = defineComponent({
  inheritAttrs: false,
  props: ['modelValue', 'min', 'max', 'step'],
  emits: ['update:modelValue'],
  template: `<input
    data-test="heat-number"
    type="number"
    :value="modelValue ?? ''"
    :min="min"
    :max="max"
    :step="step"
    @input="$emit('update:modelValue', $event.target.value === '' ? null : Number($event.target.value))"
  />`,
})

describe('平台热度等级划分', () => {
  it.each([
    [0, '淘汰素材'],
    [29.9, '淘汰素材'],
    [30, '低效素材'],
    [49.9, '低效素材'],
    [50, '普通素材'],
    [69.9, '普通素材'],
    [70, '优质素材'],
    [84.9, '优质素材'],
    [85, '超级爆款'],
    [100, '超级爆款'],
  ])('%s 分归入“%s”', (value, expected) => {
    expect(getPlatformHeatRating(value)?.name).toBe(expected)
  })

  it.each([null, undefined, -1, 101, Number.NaN])('%s 不产生等级结论', (value) => {
    expect(getPlatformHeatRating(value)).toBeNull()
  })
})

describe('平台热度输入提示', () => {
  function mountInput(value: number | null = null) {
    return mount(PlatformHeatInput, {
      props: { modelValue: value, 'onUpdate:modelValue': () => undefined, testId: 'platform-heat' },
      global: { stubs: { 'el-input-number': InputNumberStub } },
    })
  }

  it('鼠标进入时展示全部五档标准并高亮当前等级', async () => {
    const wrapper = mountInput(88)
    expect(wrapper.find('[data-test="heat-rating-guide"]').exists()).toBe(false)

    await wrapper.get('[data-test="platform-heat-field"]').trigger('mouseenter')

    expect(wrapper.findAll('[data-test="heat-rating-row"]')).toHaveLength(5)
    expect(wrapper.get('[data-test="heat-rating-guide"]').text()).toContain('重点翻拍、投放、复用')
    expect(wrapper.get('[data-test="heat-rating-row"].is-current').text()).toContain('超级爆款')
    expect(wrapper.get('[data-test="heat-current-rating"]').text()).toContain('88 · 超级爆款')
  })

  it('键盘聚焦时展示标准，0 分有效，空值不高亮', async () => {
    const wrapper = mountInput(0)

    await wrapper.get('[data-test="heat-number"]').trigger('focusin')
    expect(wrapper.get('[data-test="heat-rating-row"].is-current').text()).toContain('淘汰素材')

    await wrapper.setProps({ modelValue: null })
    expect(wrapper.find('[data-test="heat-rating-row"].is-current').exists()).toBe(false)
    expect(wrapper.find('[data-test="heat-current-rating"]').exists()).toBe(false)
  })
})
