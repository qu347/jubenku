export interface PlatformHeatRating {
  min: number
  rangeLabel: string
  name: string
  advice: string
  tone: 'excellent' | 'good' | 'normal' | 'weak' | 'discard'
}

export const PLATFORM_HEAT_RATINGS = [
  { min: 85, rangeLabel: '85～100', name: '超级爆款', advice: '重点翻拍、投放、复用', tone: 'excellent' },
  { min: 70, rangeLabel: '70～84', name: '优质素材', advice: '持续观察，适度推广', tone: 'good' },
  { min: 50, rangeLabel: '50～69', name: '普通素材', advice: '常规优化', tone: 'normal' },
  { min: 30, rangeLabel: '30～49', name: '低效素材', advice: '选题 / 封面 / 标题调整', tone: 'weak' },
  { min: 0, rangeLabel: '0～29', name: '淘汰素材', advice: '不追加资源', tone: 'discard' },
] as const satisfies readonly PlatformHeatRating[]

export function getPlatformHeatRating(value: number | null | undefined): PlatformHeatRating | null {
  if (value === null || value === undefined || !Number.isFinite(value) || value < 0 || value > 100) return null
  return PLATFORM_HEAT_RATINGS.find((rating) => value >= rating.min) ?? null
}
