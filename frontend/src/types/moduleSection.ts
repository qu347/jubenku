export type FieldType = 'text' | 'textarea' | 'markdown' | 'number' | 'date' | 'select' | 'multiselect' | 'tags' | 'image' | 'url' | 'relation'

export interface FieldDefinition {
  key: string
  label: string
  type: FieldType
  required: boolean
  sort_order: number
  options: string[]
  placeholder: string
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
  deleted_at: string | null
  material_count: number
}

export interface ModuleSectionPayload {
  section_key: string
  section_name: string
  icon: string
  sort_order: number
  enabled: boolean
  field_schema: FieldDefinition[]
  filter_schema: Record<string, unknown>
  card_schema: Record<string, unknown>
}

export interface ReorderItem {
  id: string
  sort_order: number
}
