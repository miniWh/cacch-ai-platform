import { computed, ref } from 'vue'

export type MenuIconName = 'chat' | 'list' | 'document' | 'setting' | 'menu'

export interface MenuItemConfig {
  id: string
  path: string
  title: string
  icon: MenuIconName
  /** 是否在侧栏显示 */
  visible: boolean
  /** 排序，越小越靠前 */
  sort: number
  /** 是否允许在菜单管理中隐藏（入口类可锁定） */
  locked?: boolean
}

const STORAGE_KEY = 'cacch_ai_sidebar_menus_v1'

const defaultMenus: MenuItemConfig[] = [
  { id: 'chat', path: '/chat', title: '对话台', icon: 'chat', visible: true, sort: 10, locked: true },
  { id: 'sites', path: '/sites', title: '站点清单', icon: 'list', visible: true, sort: 20 },
  { id: 'documents', path: '/documents', title: '文档与任务', icon: 'document', visible: true, sort: 30 },
  { id: 'settings', path: '/settings', title: '应用配置', icon: 'setting', visible: true, sort: 40 },
  { id: 'menus', path: '/menus', title: '菜单管理', icon: 'menu', visible: true, sort: 50 },
]

function loadMenus(): MenuItemConfig[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return structuredClone(defaultMenus)
    const parsed = JSON.parse(raw) as MenuItemConfig[]
    if (!Array.isArray(parsed) || !parsed.length) return structuredClone(defaultMenus)
    // 合并默认项，避免缺路由
    const map = new Map(parsed.map((m) => [m.id, m]))
    for (const d of defaultMenus) {
      if (!map.has(d.id)) map.set(d.id, { ...d })
    }
    return [...map.values()].sort((a, b) => a.sort - b.sort)
  } catch {
    return structuredClone(defaultMenus)
  }
}

const menus = ref<MenuItemConfig[]>(loadMenus())

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(menus.value))
}

export function useMenuStore() {
  const visibleMenus = computed(() =>
    menus.value.filter((m) => m.visible).sort((a, b) => a.sort - b.sort),
  )

  const allMenus = computed(() => [...menus.value].sort((a, b) => a.sort - b.sort))

  function setVisible(id: string, visible: boolean) {
    const item = menus.value.find((m) => m.id === id)
    if (!item || item.locked) return
    item.visible = visible
    persist()
  }

  function rename(id: string, title: string) {
    const item = menus.value.find((m) => m.id === id)
    if (!item || !title.trim()) return
    item.title = title.trim()
    persist()
  }

  function move(id: string, direction: 'up' | 'down') {
    const sorted = [...menus.value].sort((a, b) => a.sort - b.sort)
    const idx = sorted.findIndex((m) => m.id === id)
    if (idx < 0) return
    const swapWith = direction === 'up' ? idx - 1 : idx + 1
    if (swapWith < 0 || swapWith >= sorted.length) return
    const a = sorted[idx]
    const b = sorted[swapWith]
    const tmp = a.sort
    a.sort = b.sort
    b.sort = tmp
    menus.value = [...menus.value]
    persist()
  }

  function resetMenus() {
    menus.value = structuredClone(defaultMenus)
    persist()
  }

  return {
    menus,
    visibleMenus,
    allMenus,
    setVisible,
    rename,
    move,
    resetMenus,
  }
}
