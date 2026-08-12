import { request } from './http'
import type { ActiveStatus, Role } from '../types/auth'

export function listRoles(): Promise<{ items: Role[] }> {
  return request<{ items: Role[] }>('/api/v1/auth/roles')
}

export function createRole(body: {
  code: string
  name: string
  description?: string | null
  menu_ids: string[]
}): Promise<Role> {
  return request<Role>('/api/v1/auth/roles', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function updateRole(
  id: number,
  body: {
    name?: string
    description?: string | null
    status?: ActiveStatus
    menu_ids?: string[]
  },
): Promise<Role> {
  return request<Role>(`/api/v1/auth/roles/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}
