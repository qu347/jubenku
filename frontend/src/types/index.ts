export type MaterialStatus = 'draft' | 'improving' | 'completed' | 'archived'
export type SourceType = 'original' | 'excerpt' | 'ai' | 'external'

export interface Tag {
  id: string
  name: string
  material_count?: number
  created_at?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  status?: string
  material_count?: number
  created_at?: string
  updated_at?: string
}

export interface Material {
  id: string
  title: string
  material_type: string
  genre_module_id: string | null
  section_id: string | null
  genre_module: GenreModule | null
  section: ModuleSection | null
  genre: string
  summary: string
  content: string
  status: MaterialStatus
  project_id: string | null
  project: Project | null
  cover_url: string | null
  source_type: SourceType
  source_url: string | null
  favorite: boolean
  usage_count: number
  metadata: Record<string, unknown>
  tags: Tag[]
  created_at: string
  updated_at: string
  deleted_at: string | null
  version: number
}

export interface MaterialPayload {
  title: string
  material_type: string
  genre_module_id: string | null
  section_id: string | null
  genre: string
  summary: string
  content: string
  status: MaterialStatus
  project_id: string | null
  cover_url: string | null
  source_type: SourceType
  source_url: string | null
  favorite: boolean
  usage_count: number
  metadata: Record<string, unknown>
  tag_names: string[]
  change_note?: string
}

export interface MaterialVersion {
  id: string
  material_id: string
  version_number: number
  snapshot: Record<string, unknown>
  change_note: string
  created_at: string
}

export interface Pagination {
  page: number
  page_size: number
  total: number
  pages: number
}

export interface FilterOptions {
  material_types: Record<string, number>
  genres: Record<string, number>
  statuses: Record<string, number>
  projects: Project[]
  tags: Tag[]
  source_types: SourceType[]
  stats: { total: number; week_new: number; favorite: number; recently_modified: number }
  special_counts: { favorite: number; recent: number; trash: number }
  genre_modules?: GenreModule[]
  module_sections?: ModuleSection[]
}

export interface Filters {
  q: string
  type: string[]
  genre: string[]
  status: string[]
  tags: string[]
  tag_mode: 'any' | 'all'
  project_id: string[]
  source_type: string[]
  favorite: boolean | null
  used: boolean | null
  recent: boolean | null
  created_range: [string, string] | null
  updated_range: [string, string] | null
  deleted: 'active' | 'only' | 'all'
  sort: 'updated_desc' | 'created_desc' | 'usage_desc' | 'title_asc' | 'title_desc'
  page: number
  page_size: number
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  message: string
}

export type FieldType = 'text' | 'textarea' | 'markdown' | 'number' | 'date' | 'select' | 'multiselect' | 'tags' | 'image' | 'url' | 'relation'

export interface FieldDefinition {
  key: string
  label: string
  type: FieldType
  required: boolean
  options: string[]
  placeholder: string
}

export interface GenreModule {
  id: string
  name: string
  slug: string
  icon: string
  description: string
  theme_color: string
  sort_order: number
  status: 'active' | 'disabled' | 'archived'
  visible: boolean
  profile_json: Record<string, unknown>
  created_at: string
  updated_at: string
  deleted_at: string | null
  material_count: number
  section_count: number
}

export interface ModuleSection {
  id: string
  genre_module_id: string
  section_key: string
  section_name: string
  icon: string
  sort_order: number
  enabled: boolean
  field_schema: FieldDefinition[]
  filter_schema: Record<string, unknown>
  card_schema: Record<string, unknown>
  created_at: string
  updated_at: string
  material_count: number
}

export interface GenreMetric {
  id: string
  genre_module_id: string
  genre_name: string
  genre_slug: string
  theme_color: string
  platform: string
  channel: string
  period: string
  average_age: number
  age_group: '少年' | '中年' | '老年'
  education_level: '低学历' | '中学历' | '高学历'
  audience_share: number
  heat_index: number
  trend: 'rising' | 'stable' | 'falling'
  is_core: boolean
  sample_size: number
  data_source: string
  remark: string
  created_at: string
  updated_at: string
}

export type GenreMetricPayload = Omit<GenreMetric, 'id' | 'genre_name' | 'genre_slug' | 'theme_color' | 'created_at' | 'updated_at'>
