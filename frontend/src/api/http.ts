import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

interface ApiEnvelope<T> {
  success: boolean
  data: T
  message: string
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly code?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as { message?: string; detail?: string; error?: { code?: string } } | undefined
    const message = payload?.message || payload?.detail
      || (error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络请求失败，请检查后端服务')
    return new ApiError(message, error.response?.status, payload?.error?.code)
  }
  return new ApiError('发生未知错误')
}

export async function toBlobApiError(error: unknown): Promise<ApiError> {
  if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
    try {
      const blob = error.response.data
      const text = typeof blob.text === 'function'
        ? await blob.text()
        : await new Promise<string>((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '')
            reader.onerror = () => reject(reader.error)
            reader.readAsText(blob)
          })
      let payload: { message?: string; detail?: string; error?: { code?: string } } = {}
      try {
        payload = JSON.parse(text) as typeof payload
      } catch {
        if (text.trim()) payload = { message: text.trim() }
      }
      const message = payload.message || payload.detail || '文件请求失败'
      return new ApiError(message, error.response.status, payload.error?.code)
    } catch {
      return new ApiError('文件请求失败', error.response.status)
    }
  }
  return toApiError(error)
}

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await httpClient.request<ApiEnvelope<T>>(config)
    return response.data.data
  } catch (error) {
    const apiError = toApiError(error)
    ElMessage.error(apiError.message)
    throw apiError
  }
}

export async function requestBlob(config: AxiosRequestConfig): Promise<Blob> {
  try {
    const response = await httpClient.request<Blob>({ ...config, responseType: 'blob' })
    return response.data
  } catch (error) {
    const apiError = await toBlobApiError(error)
    ElMessage.error(apiError.message)
    throw apiError
  }
}
