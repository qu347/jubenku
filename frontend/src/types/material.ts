export interface MaterialGenreBrief {
  id: string
  name: string
  slug?: string
  theme_color?: string
}

export interface Material {
  id: string
  library_type?: 'material' | 'script'
  genre_module_id: string | null
  genre_module?: MaterialGenreBrief | null
  title: string
  material_type: string
  description: string
  legacy_summary?: string
  legacy_content?: string
  tags: string[]
  tags_json?: string[]
  source: string
  upload_platform: string | null
  platform_heat: number | null
  uploaded_by?: string
  project_owner?: string
  content_text?: string
  content_truncated?: boolean
  original_filename: string
  stored_filename: string
  storage_path: string
  file_extension: string
  mime_type: string
  file_size: number
  has_attachment: boolean
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type MaterialSort =
  | 'created_desc' | 'created_asc' | 'updated_desc' | 'updated_asc'
  | 'title_asc' | 'title_desc' | 'file_size_desc' | 'file_size_asc'

export interface MaterialFilters {
  library_type?: 'material' | 'script'
  keyword?: string
  genre_module_id?: string
  material_type?: string
  file_extension?: string
  tags?: string
  source?: string
  upload_platform?: string | null
  platform_heat?: number | null
  uploaded_by?: string
  uploaded_from?: string
  uploaded_to?: string
  sort?: MaterialSort
  page?: number
  page_size?: number
}

export interface MaterialPage {
  items: Material[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface MaterialUpdatePayload {
  title?: string
  genre_module_id?: string
  material_type?: string
  tags?: string[]
  tags_json?: string[]
  source?: string
  description?: string
  uploaded_by?: string
  project_owner?: string
  upload_platform?: string | null
  platform_heat?: number | null
}

interface MaterialUploadPayloadBase {
  files: File[]
  genre_module_id: string
  material_type: string
  title?: string
  tags: string[]
  source: string
  description: string
  uploaded_by?: string
  project_owner?: string
}

export type MaterialUploadPayload =
  | (MaterialUploadPayloadBase & {
    library_type?: 'material'
    upload_platform: string
    platform_heat: number
  })
  | (MaterialUploadPayloadBase & {
    library_type: 'script'
    upload_platform?: undefined
    platform_heat?: undefined
  })

export interface MaterialUploadFileResult {
  filename: string
  success: boolean
  message?: string
  error?: string
  material_id?: string
  material?: Material
}

export interface MaterialUploadResult {
  success_count: number
  failure_count: number
  results: MaterialUploadFileResult[]
  materials: Material[]
}
