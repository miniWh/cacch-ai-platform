/** Map route path to menu id for RBAC checks. */
export const PATH_MENU_MAP: Record<string, string> = {
  '/chat': 'chat',
  '/sites': 'sites',
  '/documents': 'documents',
  '/settings': 'settings',
  '/menus': 'menus',
  '/orgs': 'orgs',
  '/roles': 'roles',
  '/users': 'users',
}

export const PUBLIC_PATHS = ['/login'] as const

export const NO_MENU_CHECK_PATHS = ['/403', '/change-password'] as const
