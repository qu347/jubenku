import api from './client'
import type { ApiResponse, FieldDefinition, FilterOptions, GenreMetric, GenreMetricPayload, GenreModule, Material, MaterialPayload, MaterialVersion, ModuleSection, Pagination, Project, Tag } from '../types'

export interface MaterialQuery extends Record<string, unknown> {
  page?: number
  page_size?: number
}

export const materialApi = {
  list: (params: MaterialQuery) => api.get<ApiResponse<{ items: Material[]; pagination: Pagination }>>('/materials', { params }),
  get: (id: string) => api.get<ApiResponse<Material>>(`/materials/${id}`),
  create: (data: MaterialPayload) => api.post<ApiResponse<Material>>('/materials', data),
  update: (id: string, data: Partial<MaterialPayload>) => api.patch<ApiResponse<Material>>(`/materials/${id}`, data),
  remove: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/materials/${id}`),
  duplicate: (id: string) => api.post<ApiResponse<Material>>(`/materials/${id}/duplicate`),
  favorite: (id: string) => api.post<ApiResponse<Material>>(`/materials/${id}/favorite`),
  restore: (id: string) => api.post<ApiResponse<Material>>(`/materials/${id}/restore`),
  permanentDelete: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/materials/${id}/permanent`),
  versions: (id: string) => api.get<ApiResponse<MaterialVersion[]>>(`/materials/${id}/versions`),
  restoreVersion: (id: string, versionId: string) => api.post<ApiResponse<Material>>(`/materials/${id}/versions/${versionId}/restore`),
}

export const projectApi = {
  list: () => api.get<ApiResponse<Project[]>>('/projects'),
  create: (data: { name: string; description: string; status?: string }) => api.post<ApiResponse<Project>>('/projects', data),
  update: (id: string, data: Partial<Project>) => api.patch<ApiResponse<Project>>(`/projects/${id}`, data),
  remove: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/projects/${id}`),
}

export const tagApi = {
  list: () => api.get<ApiResponse<Tag[]>>('/tags'),
  create: (name: string) => api.post<ApiResponse<Tag>>('/tags', { name }),
  remove: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/tags/${id}`),
}

export const systemApi = {
  options: () => api.get<ApiResponse<FilterOptions>>('/filter-options'),
  importJson: (file: File) => {
    const data = new FormData()
    data.append('file', file)
    return api.post<ApiResponse<{ imported: number; failed: number }>>('/import/json', data)
  },
  exportJson: () => api.get('/export/json', { responseType: 'blob' }),
}

export const genreModuleApi = {
  list: (includeHidden = false, includeArchived = false) => api.get<ApiResponse<GenreModule[]>>('/genre-modules', { params: { include_hidden: includeHidden, include_archived: includeArchived } }),
  get: (id: string) => api.get<ApiResponse<GenreModule>>(`/genre-modules/${id}`),
  create: (data: Partial<GenreModule> & { name: string; slug: string; create_default_sections?: boolean }) => api.post<ApiResponse<GenreModule>>('/genre-modules', data),
  update: (id: string, data: Partial<GenreModule>) => api.patch<ApiResponse<GenreModule>>(`/genre-modules/${id}`, data),
  archive: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/genre-modules/${id}`),
  duplicate: (id: string) => api.post<ApiResponse<GenreModule>>(`/genre-modules/${id}/duplicate`),
  enable: (id: string) => api.post<ApiResponse<GenreModule>>(`/genre-modules/${id}/enable`),
  disable: (id: string) => api.post<ApiResponse<GenreModule>>(`/genre-modules/${id}/disable`),
  reorder: (items: Array<{ id: string; sort_order: number }>) => api.patch<ApiResponse<Array<{ id: string; sort_order: number }>>>('/genre-modules/reorder', { items }),
  sections: (id: string, includeDisabled = false) => api.get<ApiResponse<ModuleSection[]>>(`/genre-modules/${id}/sections`, { params: { include_disabled: includeDisabled } }),
  createSection: (id: string, data: Partial<ModuleSection> & { section_key: string; section_name: string }) => api.post<ApiResponse<ModuleSection>>(`/genre-modules/${id}/sections`, data),
}

export const sectionApi = {
  update: (id: string, data: Partial<ModuleSection> & { field_schema?: FieldDefinition[] }) => api.patch<ApiResponse<ModuleSection>>(`/module-sections/${id}`, data),
  remove: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/module-sections/${id}`),
  reorder: (items: Array<{ id: string; sort_order: number }>) => api.patch<ApiResponse<Array<{ id: string; sort_order: number }>>>('/module-sections/reorder', { items }),
}

export const genreMetricApi = {
  list: (params: Record<string, unknown> = {}) => api.get<ApiResponse<GenreMetric[]>>('/genre-metrics', { params }),
  create: (data: GenreMetricPayload) => api.post<ApiResponse<GenreMetric>>('/genre-metrics', data),
  update: (id: string, data: Partial<GenreMetricPayload>) => api.patch<ApiResponse<GenreMetric>>(`/genre-metrics/${id}`, data),
  remove: (id: string) => api.delete<ApiResponse<{ id: string }>>(`/genre-metrics/${id}`),
  importCsv: (file: File) => { const data = new FormData(); data.append('file', file); return api.post<ApiResponse<{ imported: number; failed: number }>>('/import/genre-metrics', data) },
  exportJson: () => api.get('/export/genre-metrics', { responseType: 'blob' }),
}
