/** Frontend runtime config (Vite env). */

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || ''

/** Optional bootstrap token only; user sessions use Bearer from login. */
export const API_AUTH_TOKEN =
  (import.meta.env.VITE_API_AUTH_TOKEN as string) || ''
