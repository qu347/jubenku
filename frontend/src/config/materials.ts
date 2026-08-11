import {
  Brush,
  ChatLineSquare,
  Collection,
  Connection,
  Film,
  Flag,
  Location,
  MagicStick,
  Reading,
  User,
} from '@element-plus/icons-vue'

export const MATERIAL_TYPES = [
  { value: 'plot', label: '故事梗概', icon: Reading, color: '#f59e0b' },
  { value: 'character', label: '人物设定', icon: User, color: '#8b5cf6' },
  { value: 'scene', label: '场景设定', icon: Location, color: '#06b6d4' },
  { value: 'conflict', label: '剧情冲突', icon: Flag, color: '#ef4444' },
  { value: 'reversal', label: '反转桥段', icon: MagicStick, color: '#ec4899' },
  { value: 'dialogue', label: '对白金句', icon: ChatLineSquare, color: '#22c55e' },
  { value: 'worldview', label: '世界观', icon: Connection, color: '#3b82f6' },
  { value: 'prop', label: '道具线索', icon: Collection, color: '#d97706' },
  { value: 'storyboard', label: '分镜镜头', icon: Film, color: '#14b8a6' },
  { value: 'reference', label: '参考资料', icon: Brush, color: '#64748b' },
] as const

export const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  improving: '完善中',
  completed: '已完成',
  archived: '已归档',
}

export const SOURCE_LABELS: Record<string, string> = {
  original: '原创',
  excerpt: '摘录',
  ai: 'AI 辅助',
  external: '外部资料',
}

export const typeInfo = (type: string) =>
  MATERIAL_TYPES.find((item) => item.value === type) || MATERIAL_TYPES[0]

export const METADATA_FIELDS: Record<string, Array<{ key: string; label: string; multiline?: boolean }>> = {
  character: [
    { key: 'name', label: '姓名' }, { key: 'age', label: '年龄' }, { key: 'gender', label: '性别' },
    { key: 'identity', label: '身份' }, { key: 'appearance', label: '外貌', multiline: true },
    { key: 'personality', label: '性格', multiline: true }, { key: 'desire', label: '欲望' },
    { key: 'goal', label: '目标' }, { key: 'weakness', label: '弱点' }, { key: 'conflict', label: '冲突', multiline: true },
    { key: 'secret', label: '秘密', multiline: true }, { key: 'character_arc', label: '人物弧光', multiline: true },
    { key: 'catchphrase', label: '口头禅' }, { key: 'relationships', label: '人物关系', multiline: true },
  ],
  scene: [
    { key: 'scene_name', label: '场景名' }, { key: 'interior_or_exterior', label: '内/外景' },
    { key: 'time', label: '时间' }, { key: 'location', label: '地点' }, { key: 'weather', label: '天气' },
    { key: 'atmosphere', label: '氛围' }, { key: 'characters', label: '出场人物' }, { key: 'objective', label: '目标' },
    { key: 'conflict', label: '冲突', multiline: true }, { key: 'outcome', label: '结果', multiline: true }, { key: 'props', label: '道具' },
  ],
  conflict: [
    { key: 'setup', label: '铺垫', multiline: true }, { key: 'trigger', label: '触发事件', multiline: true },
    { key: 'conflict', label: '核心冲突', multiline: true }, { key: 'escalation', label: '升级', multiline: true },
    { key: 'reversal', label: '反转', multiline: true }, { key: 'result', label: '结果', multiline: true },
    { key: 'foreshadowing', label: '伏笔', multiline: true }, { key: 'applicable_episode', label: '适用集数' },
  ],
  reversal: [
    { key: 'setup', label: '铺垫', multiline: true }, { key: 'trigger', label: '触发', multiline: true },
    { key: 'conflict', label: '冲突', multiline: true }, { key: 'reversal', label: '反转点', multiline: true },
    { key: 'result', label: '结果', multiline: true }, { key: 'foreshadowing', label: '前置伏笔', multiline: true },
  ],
  dialogue: [
    { key: 'speaker', label: '说话者' }, { key: 'listener', label: '倾听者' },
    { key: 'dialogue', label: '对白', multiline: true }, { key: 'tone', label: '语气' },
    { key: 'emotion', label: '情绪' }, { key: 'context', label: '语境', multiline: true },
    { key: 'subtext', label: '潜台词', multiline: true },
  ],
  storyboard: [
    { key: 'shot_number', label: '镜号' }, { key: 'shot_size', label: '景别' }, { key: 'camera_angle', label: '机位角度' },
    { key: 'camera_movement', label: '运镜' }, { key: 'visual_description', label: '画面描述', multiline: true },
    { key: 'character_action', label: '人物动作', multiline: true }, { key: 'dialogue', label: '对白', multiline: true },
    { key: 'sound', label: '声音' }, { key: 'duration', label: '时长（秒）' },
  ],
}

