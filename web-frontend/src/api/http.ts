import { API_BASE_URL } from '../config'
import { clearStoredAuth, readStoredToken } from '../stores/auth'

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

function redirectToLogin(): void {
  if (typeof window === 'undefined') return
  const path = window.location.pathname
  if (path === '/login') return
  const redirect = encodeURIComponent(path + window.location.search)
  window.location.href = `/login?redirect=${redirect}`
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Authorization')) {
    const token = readStoredToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
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
    clearStoredAuth()
    redirectToLogin()
    throw new ApiError(401, payload.message || '未授权')
  }
  if (payload.code !== 0) {
    throw new ApiError(payload.code, payload.message || '业务错误')
  }
  return payload.data
}
