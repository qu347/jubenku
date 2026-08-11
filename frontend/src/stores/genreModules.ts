import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  createGenreModule,
  deleteGenreModule,
  disableGenreModule,
  duplicateGenreModule,
  enableGenreModule,
  listGenreModules,
  reorderGenreModules,
  updateGenreModule,
} from '../api/genreModules'
import type { GenreModule, GenreModulePayload } from '../types/genreModule'
import type { ReorderItem } from '../types/moduleSection'

export const useGenreModulesStore = defineStore('genre-modules', () => {
  const modules = ref<GenreModule[]>([])
  const allModules = ref<GenreModule[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchNavigationModules() {
    loading.value = true
    error.value = null
    try {
      modules.value = await listGenreModules()
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '题材导航加载失败'
      modules.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchAllModules() {
    loading.value = true
    error.value = null
    try {
      allModules.value = await listGenreModules({ include_inactive: true, include_hidden: true })
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '题材配置加载失败'
      allModules.value = []
    } finally {
      loading.value = false
    }
  }

  async function refreshBoth() {
    await Promise.all([fetchNavigationModules(), fetchAllModules()])
  }

  async function createModule(payload: GenreModulePayload) {
    const created = await createGenreModule(payload)
    await refreshBoth()
    return created
  }

  async function updateModule(id: string, payload: Partial<GenreModulePayload>) {
    const updated = await updateGenreModule(id, payload)
    await refreshBoth()
    return updated
  }

  async function enableModule(id: string) {
    const updated = await enableGenreModule(id)
    await refreshBoth()
    return updated
  }

  async function disableModule(id: string) {
    const updated = await disableGenreModule(id)
    await refreshBoth()
    return updated
  }

  async function removeModule(id: string) {
    await deleteGenreModule(id)
    await refreshBoth()
  }

  async function duplicateModule(id: string) {
    const duplicate = await duplicateGenreModule(id)
    await refreshBoth()
    return duplicate
  }

  async function reorderModules(items: ReorderItem[]) {
    allModules.value = await reorderGenreModules(items)
    await fetchNavigationModules()
  }

  return {
    modules,
    allModules,
    loading,
    error,
    fetchNavigationModules,
    fetchAllModules,
    createModule,
    updateModule,
    enableModule,
    disableModule,
    deleteModule: removeModule,
    duplicateModule,
    reorderModules,
  }
})
