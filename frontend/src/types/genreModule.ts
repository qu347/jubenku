import type { ModuleSection } from './moduleSection'

export type GenreModuleStatus = 'active' | 'inactive' | 'disabled' | 'archived'
export type GenreLibraryType = 'material' | 'script'

export interface GenreModule {
  id: string
  name: string
  slug: string
  icon: string
  description: string
  theme_color: string
  sort_order: number
  status: GenreModuleStatus
  visible: boolean
  material_visible: boolean
  script_visible: boolean
  material_sort_order: number
  script_sort_order: number
  profile_json: Record<string, unknown>
  created_at: string
  updated_at: string
  deleted_at: string | null
  material_count: number
  script_count: number
  section_count: number
}

export interface GenreModuleDetail extends GenreModule {
  sections: ModuleSection[]
}

export interface GenreModulePayload {
  name: string
  slug: string
  icon: string
  description: string
  theme_color: string
  sort_order: number
  status: GenreModuleStatus
  visible: boolean
  material_visible?: boolean
  script_visible?: boolean
  material_sort_order?: number
  script_sort_order?: number
  profile_json: Record<string, unknown>
  create_default_sections?: boolean
}

export interface GenreModuleQuery {
  include_inactive?: boolean
  include_hidden?: boolean
  include_deleted?: boolean
  status?: GenreModuleStatus
  keyword?: string
  library_type?: GenreLibraryType
}
