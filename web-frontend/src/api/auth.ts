import { request } from './http'
import type { LoginResponse, MeResponse } from '../types/auth'

export function login(body: {
  mobile: string
  password: string
  remember_today: boolean
}): Promise<LoginResponse> {
  return request<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function logout(): Promise<void> {
  return request<void>('/api/v1/auth/logout', { method: 'POST' })
}

export function changePassword(body: {
  old_password: string
  new_password: string
}): Promise<void> {
  return request<void>('/api/v1/auth/change-password', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function fetchMe(): Promise<MeResponse> {
  return request<MeResponse>('/api/v1/auth/me')
}
