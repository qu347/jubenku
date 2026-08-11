export type AgeGroup = 'youth' | 'middle' | 'senior'
export type EducationLevel = 'low' | 'medium' | 'high'
export type MetricTrend = 'rising' | 'stable' | 'falling'

export interface GenreMetricGenreBrief {
  id: string
  name: string
  slug?: string
  theme_color?: string
}

export interface GenreMetric {
  id: string
  genre_module_id: string
  genre_module?: GenreMetricGenreBrief | null
  genre_name?: string
  genre_slug?: string
  theme_color?: string
  platform: string
  channel: string
  period: string
  average_age: number
  age_group: AgeGroup
  education_level: EducationLevel
  audience_share: number
  heat_index: number
  trend: MetricTrend
  is_core: boolean
  sample_size: number
  data_source: string
  remark: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface GenreMetricPayload {
  genre_module_id: string
  platform: string
  channel: string
  period: string
  average_age: number
  age_group: AgeGroup
  education_level: EducationLevel
  audience_share: number
  heat_index: number
  trend: MetricTrend
  is_core: boolean
  sample_size: number
  data_source: string
  remark: string
}

export interface GenreMetricFilters {
  genre_module_id?: string
  platform?: string
  channel?: string
  period?: string
  age_group?: AgeGroup
  education_level?: EducationLevel
  trend?: MetricTrend
  is_core?: boolean
  heat_min?: number
  heat_max?: number
  page?: number
  page_size?: number
}

export interface GenreMetricPage {
  items: GenreMetric[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface GenreMetricImportError {
  row: number
  field?: string
  message?: string
  reason?: string
}

export interface GenreMetricImportResult {
  success_count: number
  failure_count: number
  errors: GenreMetricImportError[]
}
