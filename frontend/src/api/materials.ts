import { request, requestBlob } from './http'
import type {
  Material, MaterialFilters, MaterialPage, MaterialUpdatePayload,
  MaterialUploadPayload, MaterialUploadResult,
} from '../types/material'

export const listMaterials = (params: MaterialFilters = {}) =>
  request<MaterialPage>({ method: 'GET', url: '/materials', params })

export const getMaterial = (id: string) =>
  request<Material>({ method: 'GET', url: `/materials/${id}` })

export const updateMaterial = (id: string, data: MaterialUpdatePayload) =>
  request<Material>({ method: 'PATCH', url: `/materials/${id}`, data })

export const deleteMaterial = (id: string) =>
  request<{ id: string }>({ method: 'DELETE', url: `/materials/${id}` })

export function uploadMaterials(payload: MaterialUploadPayload, onProgress?: (percent: number) => void) {
  const form = new FormData()
  payload.files.forEach((file) => form.append('files', file))
  form.append('library_type', payload.library_type || 'material')
  form.append('genre_module_id', payload.genre_module_id)
  form.append('material_type', payload.material_type)
  form.append('title', payload.title || '')
  form.append('tags', JSON.stringify(payload.tags))
  form.append('source', payload.source)
  form.append('description', payload.description)
  form.append('uploaded_by', payload.uploaded_by || '')
  form.append('project_owner', payload.project_owner || '')
  if (payload.upload_platform !== undefined) form.append('upload_platform', payload.upload_platform)
  if (payload.platform_heat !== undefined) form.append('platform_heat', String(payload.platform_heat))
  return request<MaterialUploadResult>({
    method: 'POST', url: '/materials/upload', data: form, timeout: 10 * 60 * 1000,
    onUploadProgress: (event) => {
      if (event.total && onProgress) onProgress(Math.round(event.loaded / event.total * 100))
    },
  })
}

export const downloadMaterial = (id: string) =>
  requestBlob({ method: 'GET', url: `/materials/${id}/download`, timeout: 2 * 60 * 1000 })
