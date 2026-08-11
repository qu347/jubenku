import { reactive, ref } from 'vue'
import { defineStore } from 'pinia'
import * as api from '../api/materials'
import type { Material, MaterialFilters, MaterialUpdatePayload, MaterialUploadPayload } from '../types/material'

const defaultFilters = (): MaterialFilters => ({ sort: 'created_desc', page: 1, page_size: 20 })

export const useMaterialsStore = defineStore('materials', () => {
  const items = ref<Material[]>([])
  const total = ref(0)
  const pages = ref(0)
  const filters = reactive<MaterialFilters>(defaultFilters())
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchMaterials() {
    loading.value = true
    error.value = null
    try {
      const result = await api.listMaterials({ ...filters })
      items.value = result.items
      total.value = result.total
      pages.value = result.pages
      filters.page = result.page
      filters.page_size = result.page_size
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '素材列表加载失败'
      items.value = []
    } finally {
      loading.value = false
    }
  }

  function setFilters(next: MaterialFilters) {
    Object.assign(filters, defaultFilters(), next)
  }

  function resetFilters() {
    Object.assign(filters, defaultFilters())
  }

  async function upload(payload: MaterialUploadPayload, onProgress?: (percent: number) => void) {
    const result = await api.uploadMaterials(payload, onProgress)
    await fetchMaterials()
    return result
  }

  async function update(id: string, payload: MaterialUpdatePayload) {
    const updated = await api.updateMaterial(id, payload)
    const index = items.value.findIndex((item) => item.id === id)
    if (index >= 0) items.value[index] = updated
    return updated
  }

  async function remove(id: string) {
    await api.deleteMaterial(id)
    await fetchMaterials()
  }

  return { items, total, pages, filters, loading, error, fetchMaterials, setFilters, resetFilters, upload, update, remove }
})
