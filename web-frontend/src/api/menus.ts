import { request } from './http'
import type { MenuRecord } from '../types/auth'

export function listMenus(): Promise<{ items: MenuRecord[] }> {
  return request<{ items: MenuRecord[] }>('/api/v1/auth/menus')
}
