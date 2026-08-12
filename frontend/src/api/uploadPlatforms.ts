import { request } from './http'
import type { UploadPlatform } from '../types/uploadPlatform'

export const listUploadPlatforms = () =>
  request<UploadPlatform[]>({ method: 'GET', url: '/upload-platforms' })

export const createUploadPlatform = (name: string) =>
  request<UploadPlatform>({ method: 'POST', url: '/upload-platforms', data: { name } })
