import { request, requestBlob } from './http'
import type {
  GenreMetric, GenreMetricFilters, GenreMetricImportResult,
  GenreMetricPage, GenreMetricPayload,
} from '../types/genreMetric'

export const listGenreMetrics = (params: GenreMetricFilters = {}) =>
  request<GenreMetricPage>({ method: 'GET', url: '/genre-metrics', params })

export const getGenreMetric = (id: string) =>
  request<GenreMetric>({ method: 'GET', url: `/genre-metrics/${id}` })

export const createGenreMetric = (data: GenreMetricPayload) =>
  request<GenreMetric>({ method: 'POST', url: '/genre-metrics', data })

export const updateGenreMetric = (id: string, data: Partial<GenreMetricPayload>) =>
  request<GenreMetric>({ method: 'PATCH', url: `/genre-metrics/${id}`, data })

export const deleteGenreMetric = (id: string) =>
  request<{ id: string }>({ method: 'DELETE', url: `/genre-metrics/${id}` })

export function importGenreMetrics(file: File) {
  const form = new FormData()
  form.append('file', file)
  return request<GenreMetricImportResult>({ method: 'POST', url: '/genre-metrics/import', data: form, timeout: 5 * 60 * 1000 })
}

export const downloadGenreMetricTemplate = (format: 'xlsx' | 'csv' = 'xlsx') =>
  requestBlob({ method: 'GET', url: '/genre-metrics/import-template', params: { format }, timeout: 60_000 })

export const exportGenreMetrics = (params: GenreMetricFilters, format: 'xlsx' | 'csv') =>
  requestBlob({ method: 'GET', url: '/genre-metrics/export', params: { ...params, format }, timeout: 2 * 60 * 1000 })
