import { request } from './http'
import type { ActiveStatus, AuthUser, HrPreview, UserListItem } from '../types/auth'

export function listUsers(params?: {
  keyword?: string
  org_id?: number
  status?: ActiveStatus
}): Promise<{ items: UserListItem[]; total: number }> {
  const qs = new URLSearchParams()
  if (params?.keyword) qs.set('keyword', params.keyword)
  if (params?.org_id !== undefined) qs.set('org_id', String(params.org_id))
  if (params?.status) qs.set('status', params.status)
  const query = qs.toString()
  return request<{ items: UserListItem[]; total: number }>(
    `/api/v1/auth/users${query ? `?${query}` : ''}`,
  )
}

export function previewHr(mobile: string): Promise<HrPreview> {
  return request<HrPreview>('/api/v1/auth/users/preview-hr', {
    method: 'POST',
    body: JSON.stringify({ mobile }),
  })
}

export function createUser(body: {
  mobile: string
  org_id: number
  role_id?: number | null
  menu_ids?: string[]
  password?: string
  generate_password?: boolean
  remark?: string | null
}): Promise<{ user: AuthUser; plain_password: string | null }> {
  return request<{ user: AuthUser; plain_password: string | null }>(
    '/api/v1/auth/users',
    {
      method: 'POST',
      body: JSON.stringify(body),
    },
  )
}

export function updateUser(
  id: number,
  body: {
    org_id?: number
    role_id?: number | null
    menu_ids?: string[]
    status?: ActiveStatus
    remark?: string | null
  },
): Promise<UserListItem> {
  return request<UserListItem>(`/api/v1/auth/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function resetPassword(
  id: number,
  body?: { password?: string; generate_password?: boolean },
): Promise<{ plain_password: string }> {
  return request<{ plain_password: string }>(
    `/api/v1/auth/users/${id}/reset-password`,
    {
      method: 'POST',
      body: JSON.stringify(body ?? { generate_password: true }),
    },
  )
}
