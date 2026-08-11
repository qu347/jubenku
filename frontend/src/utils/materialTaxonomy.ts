export type StandardTagGroupKey = 'plot' | 'emotion' | 'era' | 'role'

export interface StandardTagGroup {
  key: StandardTagGroupKey
  label: string
  multiple: boolean
  options: string[]
}

export const standardTagGroups: StandardTagGroup[] = [
  {
    key: 'plot', label: '剧情', multiple: true,
    options: ['逆袭', '马甲', '亲情', '穿越', '重生', '战神归来', '豪婿逆袭', '异能', '无敌神医', '传承觉醒', '系统', '穿书', '娱乐圈', '打脸虐渣', '豪门恩怨', '女性成长', '闪婚', '古风权谋', '奇幻爱情', '虐恋', '追妻', '暗恋成真', '现言甜宠', '破镜重圆', '年代爱情', '先婚后爱', '强制爱', '复仇', '犯罪', '多反转'],
  },
  {
    key: 'emotion', label: '情绪', multiple: true,
    options: ['甜宠', '虐恋', '轻松', '紧张', '温馨', '感动', '惊悚', '欢喜', '忧伤', '治愈', '搞笑', '热血', '狗血', '激情', '悲壮', '浪漫'],
  },
  {
    key: 'era', label: '时代背景', multiple: false,
    options: ['现代', '近代', '古代', '未来', '架空'],
  },
  {
    key: 'role', label: '角色设定', multiple: true,
    options: ['神豪', '小人物', '强者回归', '天下无敌', '高手下山', '女帝', '龙王', '总裁', '大女主', '萌宝', '王妃', '真假千金', '强强联合', '皇后', '青梅竹马', '欢喜冤家', '团宠', '大叔', '替身', '绿茶', '白莲花', '危险偏执男主', '病娇'],
  },
]

const prefixes = Object.fromEntries(standardTagGroups.map((group) => [group.label, group]))

export function decodeStandardTags(tags: string[]) {
  const selections: Record<StandardTagGroupKey, string[]> = { plot: [], emotion: [], era: [], role: [] }
  const passthrough: string[] = []
  for (const tag of tags) {
    const [prefix, ...rest] = tag.split(':')
    const value = rest.join(':')
    const prefixedGroup = prefixes[prefix]
    if (prefixedGroup && prefixedGroup.options.includes(value)) {
      selections[prefixedGroup.key].push(value)
      continue
    }
    const matched = standardTagGroups.find((group) => group.options.includes(tag))
    if (matched) selections[matched.key].push(tag)
    else passthrough.push(tag)
  }
  return { selections, passthrough }
}

export function encodeStandardTags(
  selections: Record<StandardTagGroupKey, string[]>,
  passthrough: string[] = [],
) {
  return [
    ...standardTagGroups.flatMap((group) => selections[group.key].map((value) => `${group.label}:${value}`)),
    ...passthrough,
  ]
}

export function readableTag(tag: string) {
  const separator = tag.indexOf(':')
  return separator >= 0 ? tag.slice(separator + 1) : tag
}
