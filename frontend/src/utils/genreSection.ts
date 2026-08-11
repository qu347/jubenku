const SECTION_MATERIAL_ALIASES: Record<string, string[]> = {
  elements: ['elements', 'element', 'prop', '创作元素', '道具线索'],
  characters: ['characters', 'character', '人物素材', '人物设定'],
  plots: ['plots', 'plot', 'conflict', 'reversal', 'storyboard', '剧情素材', '剧情桥段', '故事梗概', '剧情冲突', '反转桥段', '分镜镜头'],
  scenes: ['scenes', 'scene', '场景素材', '场景设定', '场景参考'],
  dialogues: ['dialogues', 'dialogue', '对白素材', '对白金句'],
  worldview: ['worldview', '世界观素材', '世界观'],
  references: ['references', 'reference', 'research', '参考资料', '研究资料'],
}

const SECTION_UPLOAD_TYPES: Record<string, string> = {
  overview: '研究资料',
  elements: '创作元素',
  characters: '人物素材',
  plots: '剧情素材',
  scenes: '场景素材',
  dialogues: '对白素材',
  worldview: '世界观素材',
  references: '参考资料',
}

function normalize(value: string) {
  return value.trim().toLocaleLowerCase()
}

export function sectionMaterialAliases(sectionKey: string, sectionName: string): string[] {
  const values = [...(SECTION_MATERIAL_ALIASES[sectionKey] || []), sectionKey, sectionName]
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))]
}

export function materialBelongsToSection(
  materialType: string,
  sectionKey: string,
  sectionName: string,
): boolean {
  if (sectionKey === 'overview') return true
  if (sectionKey === 'audience') return false
  const target = normalize(materialType)
  return sectionMaterialAliases(sectionKey, sectionName).some((value) => normalize(value) === target)
}

export function defaultMaterialTypeForSection(sectionKey: string, sectionName: string): string {
  return SECTION_UPLOAD_TYPES[sectionKey] || sectionName
}
