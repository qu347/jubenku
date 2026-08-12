export interface GenrePositioningItem {
  genre_module_id: string
  genre_name: string
  theme_color: string
  upload_platform: string
  average_heat: number
  material_count: number
  latest_updated_at: string
}

export interface GenrePositioningList {
  items: GenrePositioningItem[]
  total: number
}

export interface GenrePositioningTimelinePoint {
  genre_module_id: string
  genre_name: string
  theme_color: string
  period: string
  average_heat: number
  material_count: number
}

export interface GenrePositioningTimeline {
  upload_platform: string
  periods: string[]
  points: GenrePositioningTimelinePoint[]
  total_materials: number
}

