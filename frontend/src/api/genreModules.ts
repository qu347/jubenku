import { request } from './http'
import type { GenreModule, GenreModuleDetail, GenreModulePayload, GenreModuleQuery } from '../types/genreModule'
import type { ModuleSection, ModuleSectionPayload, ReorderItem } from '../types/moduleSection'

export const listGenreModules = (params: GenreModuleQuery = {}) =>
  request<GenreModule[]>({ method: 'GET', url: '/genre-modules', params })

export const getGenreModule = (id: string) =>
  request<GenreModule>({ method: 'GET', url: `/genre-modules/${id}` })

export const getGenreModuleBySlug = (slug: string, includeDisabled = false) =>
  request<GenreModuleDetail>({
    method: 'GET',
    url: `/genre-modules/slug/${encodeURIComponent(slug)}`,
    params: { include_disabled: includeDisabled },
  })

export const createGenreModule = (data: GenreModulePayload) =>
  request<GenreModule>({ method: 'POST', url: '/genre-modules', data })

export const updateGenreModule = (id: string, data: Partial<GenreModulePayload>) =>
  request<GenreModule>({ method: 'PATCH', url: `/genre-modules/${id}`, data })

export const deleteGenreModule = (id: string) =>
  request<{ id: string }>({ method: 'DELETE', url: `/genre-modules/${id}` })

export const duplicateGenreModule = (id: string) =>
  request<GenreModule>({ method: 'POST', url: `/genre-modules/${id}/duplicate` })

export const enableGenreModule = (id: string) =>
  request<GenreModule>({ method: 'POST', url: `/genre-modules/${id}/enable` })

export const disableGenreModule = (id: string) =>
  request<GenreModule>({ method: 'POST', url: `/genre-modules/${id}/disable` })

export const reorderGenreModules = (items: ReorderItem[]) =>
  request<GenreModule[]>({ method: 'PATCH', url: '/genre-modules/batch/reorder', data: { items } })

export const listModuleSections = (moduleId: string, includeDisabled = false) =>
  request<ModuleSection[]>({
    method: 'GET',
    url: `/genre-modules/${moduleId}/sections`,
    params: { include_disabled: includeDisabled },
  })

export const createModuleSection = (moduleId: string, data: ModuleSectionPayload) =>
  request<ModuleSection>({ method: 'POST', url: `/genre-modules/${moduleId}/sections`, data })
