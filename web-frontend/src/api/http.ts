import { API_AUTH_TOKEN, API_BASE_URL } from '../config'

export class ApiError extends Error {
  code: number

  constructor(code: number, message: string) {
    super(message)
    this.code = code
  }
}

interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${API_AUTH_TOKEN}`)
  }
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })

  let payload: ApiEnvelope<T>
  try {
    payload = (await res.json()) as ApiEnvelope<T>
  } catch {
    throw new ApiError(res.status, `请求失败（HTTP ${res.status}）`)
  }

  if (res.status === 401 || payload.code === 401) {
    throw new ApiError(401, payload.message || '未授权')
  }
  if (payload.code !== 0) {
    throw new ApiError(payload.code, payload.message || '业务错误')
  }
  return payload.data
}
