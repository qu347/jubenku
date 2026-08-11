import { describe, expect, it } from 'vitest'
import {
  defaultMaterialTypeForSection,
  materialBelongsToSection,
  sectionMaterialAliases,
} from '../utils/genreSection'

describe('题材板块素材归类', () => {
  it('兼容历史英文类型与新版中文类型', () => {
    expect(materialBelongsToSection('characters', 'characters', '人物素材')).toBe(true)
    expect(materialBelongsToSection('人物设定', 'characters', '人物素材')).toBe(true)
    expect(materialBelongsToSection('研究资料', 'characters', '人物素材')).toBe(false)
    expect(materialBelongsToSection('研究资料', 'references', '参考资料')).toBe(true)
    expect(materialBelongsToSection('conflict', 'plots', '剧情素材')).toBe(true)
  })

  it('自定义板块使用板块名称归类并预填上传类型', () => {
    expect(sectionMaterialAliases('creatures', '怪物图鉴')).toContain('怪物图鉴')
    expect(materialBelongsToSection('怪物图鉴', 'creatures', '怪物图鉴')).toBe(true)
    expect(defaultMaterialTypeForSection('creatures', '怪物图鉴')).toBe('怪物图鉴')
    expect(defaultMaterialTypeForSection('characters', '人物素材')).toBe('人物素材')
  })
})
