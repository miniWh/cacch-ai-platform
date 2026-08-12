import { computed, ref } from 'vue'
import * as authApi from '../api/auth'
import * as menusApi from '../api/menus'
import type { AuthPersist, AuthUser, MenuRecord } from '../types/auth'

export const AUTH_STORAGE_KEY = 'cacch_ai_auth_v1'

export function readStoredAuth(): AuthPersist | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthPersist
    if (!parsed.access_token || !parsed.user) return null
    return parsed
  } catch {
    return null
  }
}

export function readStoredToken(): string | null {
  return readStoredAuth()?.access_token ?? null
}

export function clearStoredAuth(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

function persist(data: AuthPersist): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data))
}

const stored = readStoredAuth()

const accessToken = ref<string | null>(stored?.access_token ?? null)
const expiresAt = ref<string | null>(stored?.expires_at ?? null)
const user = ref<AuthUser | null>(stored?.user ?? null)
const mustChangePassword = ref(stored?.must_change_password ?? false)
const menuCatalog = ref<MenuRecord[]>([])

let bootstrapPromise: Promise<void> | null = null

function applySession(data: {
  access_token: string
  expires_at: string
  must_change_password: boolean
  user: AuthUser
}): void {
  accessToken.value = data.access_token
  expiresAt.value = data.expires_at
  user.value = data.user
  mustChangePassword.value = data.must_change_password
  persist({
    access_token: data.access_token,
    expires_at: data.expires_at,
    must_change_password: data.must_change_password,
    user: data.user,
  })
}

export function useAuthStore() {
  const isAuthenticated = computed(() => Boolean(accessToken.value && user.value))

  const sidebarMenus = computed(() => {
    const ids = new Set(user.value?.menu_ids ?? [])
    return menuCatalog.value
      .filter((m) => ids.has(m.id) && m.status === 'active')
      .sort((a, b) => a.sort_order - b.sort_order)
  })

  async function loadMenuCatalog(): Promise<void> {
    const res = await menusApi.listMenus()
    menuCatalog.value = res.items
  }

  async function login(
    mobile: string,
    password: string,
    rememberToday: boolean,
  ): Promise<void> {
    const res = await authApi.login({ mobile, password, remember_today: rememberToday })
    applySession(res)
    await loadMenuCatalog()
  }

  async function fetchMe(): Promise<void> {
    const res = await authApi.fetchMe()
    if (!accessToken.value) return
    user.value = {
      id: res.id,
      staff_no: res.staff_no,
      mobile: res.mobile,
      name: res.name,
      email: res.email,
      menu_ids: res.menu_ids,
    }
    mustChangePassword.value = res.must_change_password
    persist({
      access_token: accessToken.value,
      expires_at: expiresAt.value ?? '',
      must_change_password: res.must_change_password,
      user: user.value,
    })
  }

  async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await authApi.changePassword({
      old_password: oldPassword,
      new_password: newPassword,
    })
    mustChangePassword.value = false
    if (accessToken.value && user.value) {
      persist({
        access_token: accessToken.value,
        expires_at: expiresAt.value ?? '',
        must_change_password: false,
        user: user.value,
      })
    }
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      /* ignore logout errors */
    }
    clearAuth()
  }

  function clearAuth(): void {
    accessToken.value = null
    expiresAt.value = null
    user.value = null
    mustChangePassword.value = false
    menuCatalog.value = []
    clearStoredAuth()
  }

  async function bootstrap(): Promise<void> {
    if (!isAuthenticated.value) return
    if (!bootstrapPromise) {
      bootstrapPromise = (async () => {
        try {
          await fetchMe()
          await loadMenuCatalog()
        } catch {
          clearAuth()
        } finally {
          bootstrapPromise = null
        }
      })()
    }
    await bootstrapPromise
  }

  function hasMenu(menuId: string): boolean {
    return (user.value?.menu_ids ?? []).includes(menuId)
  }

  return {
    accessToken,
    expiresAt,
    user,
    mustChangePassword,
    menuCatalog,
    isAuthenticated,
    sidebarMenus,
    login,
    logout,
    fetchMe,
    changePassword,
    loadMenuCatalog,
    clearAuth,
    bootstrap,
    hasMenu,
  }
}
