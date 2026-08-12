import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getGenrePositioningTimeline, listGenrePositioning } from '../api/genrePositioning'
import { useUploadPlatformsStore } from './uploadPlatforms'
import type { GenrePositioningTimeline } from '../types/genrePositioning'

const emptyTimeline = (): GenrePositioningTimeline => ({
  upload_platform: '',
  periods: [],
  points: [],
  total_materials: 0,
})

export const ALL_PLATFORMS = '全部平台'

function platformKey(value: string) {
  return value.trim().normalize('NFKC').toLocaleLowerCase()
}

export const useGenrePositioningStore = defineStore('genre-positioning', () => {
  const uploadPlatformCatalog = useUploadPlatformsStore()
  const platforms = ref<string[]>([])
  const selectedPlatform = ref('')
  const timeline = ref<GenrePositioningTimeline>(emptyTimeline())
  const loading = ref(false)
  const error = ref<string | null>(null)
  let requestToken = 0

  async function fetchPlatforms(preferredPlatform?: string) {
    loading.value = true
    error.value = null
    try {
      await uploadPlatformCatalog.fetchPlatforms().catch(() => undefined)
      const result = await listGenrePositioning()
      const unique = new Map<string, string>()
      for (const platform of uploadPlatformCatalog.platforms) {
        const display = platform.trim()
        const key = platformKey(display)
        if (key && !unique.has(key)) unique.set(key, display)
      }
      for (const item of result.items) {
        const display = item.upload_platform.trim()
        const key = platformKey(display)
        if (key && !unique.has(key)) unique.set(key, display)
      }
      platforms.value = [ALL_PLATFORMS, ...[...unique.values()].sort((a, b) => a.localeCompare(b, 'zh-CN'))]
      const preferredKey = platformKey(preferredPlatform || '')
      const currentKey = platformKey(selectedPlatform.value)
      const next = (preferredKey && platforms.value.find((item) => platformKey(item) === preferredKey))
        || platforms.value.find((item) => platformKey(item) === currentKey)
        || ALL_PLATFORMS
      await selectPlatform(next)
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '平台数据加载失败'
      platforms.value = []
      selectedPlatform.value = ''
      timeline.value = emptyTimeline()
    } finally {
      loading.value = false
    }
  }

  async function selectPlatform(platform: string) {
    const value = platform.trim() || ALL_PLATFORMS
    selectedPlatform.value = value
    const token = ++requestToken
    loading.value = true
    error.value = null
    try {
      const result = await getGenrePositioningTimeline(value === ALL_PLATFORMS ? undefined : value)
      if (token === requestToken) {
        timeline.value = result
        selectedPlatform.value = result.upload_platform
      }
    } catch (reason) {
      if (token === requestToken) {
        error.value = reason instanceof Error ? reason.message : '月度热度加载失败'
        timeline.value = emptyTimeline()
      }
    } finally {
      if (token === requestToken) loading.value = false
    }
  }

  return { platforms, selectedPlatform, timeline, loading, error, fetchPlatforms, selectPlatform }
})

