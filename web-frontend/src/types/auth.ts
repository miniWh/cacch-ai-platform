export interface AuthUser {
  id: number
  staff_no: string
  mobile: string
  name: string
  email: string | null
  menu_ids: string[]
  must_change_password?: boolean
}

export interface LoginResponse {
  access_token: string
  expires_at: string
  must_change_password: boolean
  user: AuthUser
}

export interface MeResponse extends AuthUser {
  must_change_password: boolean
}

export type ActiveStatus = 'active' | 'disabled'

export interface MenuRecord {
  id: string
  title: string
  path: string
  icon: string | null
  sort_order: number
  status: ActiveStatus
}

export interface Org {
  id: number
  parent_id: number | null
  code: string | null
  name: string
  sort_order: number
  status: ActiveStatus
  remark: string | null
}

export interface Role {
  id: number
  code: string
  name: string
  description: string | null
  status: ActiveStatus
  menu_ids: string[]
}

export interface UserListItem {
  id: number
  staff_no: string
  mobile: string
  name: string
  email: string | null
  staff_status: string
  org_id: number
  org_name?: string | null
  role_id: number | null
  role_name?: string | null
  status: ActiveStatus
  must_change_password: boolean
  menu_ids: string[]
  last_login_at: string | null
}

export interface HrPreview {
  staff_no: string
  mobile: string
  name: string
  email: string | null
  staff_status: string
}

export interface AuthPersist {
  access_token: string
  expires_at: string
  must_change_password: boolean
  user: AuthUser
}
