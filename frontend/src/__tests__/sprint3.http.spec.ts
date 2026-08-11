import { describe, expect, it } from 'vitest'
import { toBlobApiError } from '../api/http'

describe('Blob 下载错误解析', () => {
  it('保留后端 JSON 错误消息、状态码和错误码', async () => {
    const error = {
      isAxiosError: true,
      response: {
        status: 422,
        data: new Blob([JSON.stringify({ message: '导出筛选条件无效', error: { code: 'invalid_filter' } })], { type: 'application/json' }),
      },
    }
    const parsed = await toBlobApiError(error)
    expect(parsed.message).toBe('导出筛选条件无效')
    expect(parsed.status).toBe(422)
    expect(parsed.code).toBe('invalid_filter')
  })
})
