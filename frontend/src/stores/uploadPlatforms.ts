import { ref } from 'vue'
import { defineStore } from 'pinia'
import { createUploadPlatform, listUploadPlatforms } from '../api/uploadPlatforms'
import { ApiError } from '../api/http'
import { COMMON_UPLOAD_PLATFORMS } from '../config/materials'

export function uploadPlatformKey(value: string) {
  return value.trim().normalize('NFKC').toLocaleLowerCase()
}

export const useUploadPlatformsStore = defineStore('upload-platforms', () => {
  const platforms = ref<string[]>([...COMMON_UPLOAD_PLATFORMS])
  const loading = ref(false)
  let loaded = false
  let pending: Promise<void> | null = null

  function mergePlatforms(values: readonly string[]) {
    const unique = new Map<string, string>()
    for (const value of [...platforms.value, ...values]) {
      const display = value.trim().normalize('NFKC')
      const key = uploadPlatformKey(display)
      if (key && !unique.has(key)) unique.set(key, display)
    }
    platforms.value = [...unique.values()]
  }

  async function fetchPlatforms(force = false): Promise<void> {
    if (loaded && !force) return
    if (pending && !force) return pending
    loading.value = true
    const activeRequest = listUploadPlatforms()
      .then((items) => {
        mergePlatforms(items.map((item) => item.name))
        loaded = true
      })
      .finally(() => {
        loading.value = false
        pending = null
      })
    pending = activeRequest
    return activeRequest
  }

  async function createPlatform(name: string): Promise<string> {
    const display = name.trim().normalize('NFKC')
    try {
      const created = await createUploadPlatform(display)
      mergePlatforms([created.name])
      return created.name
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        await fetchPlatforms(true)
        const existing = platforms.value.find((item) => uploadPlatformKey(item) === uploadPlatformKey(display))
        if (existing) return existing
      }
      throw error
    }
  }

  return { platforms, loading, fetchPlatforms, createPlatform }
})
