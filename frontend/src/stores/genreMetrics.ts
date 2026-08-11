import { reactive, ref } from 'vue'
import { defineStore } from 'pinia'
import * as api from '../api/genreMetrics'
import type { GenreMetric, GenreMetricFilters, GenreMetricPayload } from '../types/genreMetric'

const defaultFilters = (): GenreMetricFilters => ({ heat_min: 0, heat_max: 100, page: 1, page_size: 100 })

export const useGenreMetricsStore = defineStore('genre-metrics', () => {
  const items = ref<GenreMetric[]>([])
  const total = ref(0)
  const pages = ref(0)
  const filters = reactive<GenreMetricFilters>(defaultFilters())
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchMetrics() {
    loading.value = true
    error.value = null
    try {
      const first = await api.listGenreMetrics({ ...filters, page: 1, page_size: 100 })
      const remaining = first.pages > 1
        ? await Promise.all(Array.from({ length: first.pages - 1 }, (_, index) => api.listGenreMetrics({ ...filters, page: index + 2, page_size: 100 })))
        : []
      items.value = [first, ...remaining].flatMap((page) => page.items)
      total.value = first.total
      pages.value = first.pages
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '定位数据加载失败'
      items.value = []
    } finally {
      loading.value = false
    }
  }

  function setFilters(next: GenreMetricFilters) { Object.assign(filters, defaultFilters(), next) }
  function resetFilters() { Object.assign(filters, defaultFilters()) }

  async function create(payload: GenreMetricPayload) {
    const created = await api.createGenreMetric(payload)
    await fetchMetrics()
    return created
  }
  async function update(id: string, payload: Partial<GenreMetricPayload>) {
    const updated = await api.updateGenreMetric(id, payload)
    await fetchMetrics()
    return updated
  }
  async function remove(id: string) {
    await api.deleteGenreMetric(id)
    await fetchMetrics()
  }

  return { items, total, pages, filters, loading, error, fetchMetrics, setFilters, resetFilters, create, update, remove }
})
