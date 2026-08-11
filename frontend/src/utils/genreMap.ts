import type { EducationLevel, GenreMetric } from '../types/genreMetric'

export const EDUCATION_SCORE: Record<EducationLevel, number> = { low: 1, medium: 2, high: 3 }
export const EDUCATION_LABEL: Record<EducationLevel, string> = { low: '低学历', medium: '中学历', high: '高学历' }
export const AGE_LABEL = { youth: '少年', middle: '中年', senior: '老年' } as const

export function weightedMean(items: GenreMetric[], selector: (item: GenreMetric) => number): number {
  if (!items.length) return 0
  const weight = items.reduce((sum, item) => sum + Math.max(item.audience_share, 0), 0)
  if (weight > 0) return items.reduce((sum, item) => sum + selector(item) * Math.max(item.audience_share, 0), 0) / weight
  return items.reduce((sum, item) => sum + selector(item), 0) / items.length
}

export function bubbleSize(share: number): number {
  return Math.max(20, Math.min(82, 18 + Math.sqrt(Math.max(share, 0)) * 7))
}

export function regionShare(items: GenreMetric[], ageGroup: GenreMetric['age_group'], education: EducationLevel): number {
  return items.filter((item) => item.age_group === ageGroup && item.education_level === education)
    .reduce((sum, item) => sum + item.audience_share, 0)
}
