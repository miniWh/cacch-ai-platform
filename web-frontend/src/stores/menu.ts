import { computed } from 'vue'
import { useAuthStore } from './auth'

export type MenuIconName =
  | 'chat'
  | 'list'
  | 'document'
  | 'setting'
  | 'menu'
  | 'office'
  | 'key'
  | 'user'

const SERVER_ICON_MAP: Record<string, MenuIconName> = {
  chat: 'chat',
  list: 'list',
  document: 'document',
  setting: 'setting',
  menu: 'menu',
  orgs: 'office',
  roles: 'key',
  users: 'user',
}

export function resolveMenuIcon(serverIcon: string | null, menuId: string): MenuIconName {
  if (serverIcon) {
    const mapped = SERVER_ICON_MAP[serverIcon]
    if (mapped) return mapped
  }
  return SERVER_ICON_MAP[menuId] ?? 'menu'
}

export interface SidebarMenuItem {
  id: string
  path: string
  title: string
  icon: MenuIconName
  sort: number
}

export function useMenuStore() {
  const auth = useAuthStore()

  const visibleMenus = computed<SidebarMenuItem[]>(() =>
    auth.sidebarMenus.value.map((m) => ({
      id: m.id,
      path: m.path,
      title: m.title,
      icon: resolveMenuIcon(m.icon, m.id),
      sort: m.sort_order,
    })),
  )

  const allMenus = computed(() => auth.menuCatalog.value)

  return {
    visibleMenus,
    allMenus,
  }
}
