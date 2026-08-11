import { describe, expect, it } from 'vitest'
import { isValidGenreSlug } from '../utils/validation'

describe('模块设置表单校验', () => {
  it('校验 slug 仅允许小写字母、数字和连字符', () => {
    expect(isValidGenreSlug('rule-horror')).toBe(true)
    expect(isValidGenreSlug('rule-horror-2')).toBe(true)
    expect(isValidGenreSlug('Rule-Horror')).toBe(false)
    expect(isValidGenreSlug('rule_horror')).toBe(false)
  })
})
