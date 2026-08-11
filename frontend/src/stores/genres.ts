import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { genreModuleApi } from '../api'
import type { GenreModule } from '../types'

export const useGenresStore = defineStore('genres', () => {
  const modules = ref<GenreModule[]>([])
  const allModules = ref<GenreModule[]>([])
  const loading = ref(false)
  const activeModules = computed(() => modules.value.filter((item) => item.status === 'active' && item.visible))

  async function fetchModules() {
    loading.value = true
    try { modules.value = (await genreModuleApi.list()).data.data }
    finally { loading.value = false }
  }

  async function fetchAllModules() {
    allModules.value = (await genreModuleApi.list(true, true)).data.data
  }

  function bySlug(slug: string) { return modules.value.find((item) => item.slug === slug) }
  return { modules, allModules, activeModules, loading, fetchModules, fetchAllModules, bySlug }
})
