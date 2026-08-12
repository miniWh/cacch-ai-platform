import { request } from './http'
import type { ActiveStatus, Org } from '../types/auth'

export function listOrgs(): Promise<{ items: Org[] }> {
  return request<{ items: Org[] }>('/api/v1/auth/orgs')
}

export function createOrg(body: {
  parent_id?: number | null
  code?: string
  name: string
  sort_order?: number
  status?: ActiveStatus
  remark?: string | null
}): Promise<Org> {
  return request<Org>('/api/v1/auth/orgs', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function updateOrg(
  id: number,
  body: {
    parent_id?: number | null
    code?: string
    name?: string
    sort_order?: number
    status?: ActiveStatus
    remark?: string | null
  },
): Promise<Org> {
  return request<Org>(`/api/v1/auth/orgs/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}
