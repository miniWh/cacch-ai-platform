export type RegionCode = 'US' | 'EU' | 'UK' | 'AU' | 'JP' | 'CN' | 'INT'
export type SiteCategory = 'registration' | 'evaluation' | 'standard' | 'database'
export type CrawlMode = 'manual' | 'single_page' | 'list_harvest' | 'connector'
export type SiteStatus = 'active' | 'broken' | 'pending_url' | 'disabled'

export interface SourceSite {
  site_id: string
  kb_id: number
  name: string
  region: RegionCode
  category: SiteCategory
  entry_url: string | null
  crawl_mode: CrawlMode
  allowed_domains: string[]
  rate_limit_qps?: number | null
  status: SiteStatus
  notes: string | null
  last_probe_at: string | null
  last_probe_status: string | null
  created_at?: string
  updated_at?: string
}

export interface KnowledgeBase {
  id: number
  name: string
  description: string | null
  embedding_model: string
  embedding_dim: number
  status: number
  created_at: string
  updated_at: string
}

export interface Citation {
  index: number
  title: string
  site_name: string
  url: string
  snippet: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  time: string
  citations?: Citation[]
}

/** Backend session list/detail shape */
export interface ChatSessionApi {
  session_id: string
  kb_id: number
  app_id: number | null
  user_id: string | null
  title: string
  title_locked: boolean
  pinned: boolean
  pinned_at: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessageApi {
  message_id: string
  session_id: string
  role: string
  content: string
  citations?: Citation[] | null
  created_at: string
}

export interface ChatSessionDetailApi extends ChatSessionApi {
  messages: ChatMessageApi[]
}

export interface ChatSession {
  id: string
  title: string
  title_locked: boolean
  pinned: boolean
  time_label: string
  updated_at: string
  messages: ChatMessage[]
}

export interface AppInfo {
  id: number
  name: string
  app_type: string
  model_profile_id: string
  kb_name: string
  kb_count: number
}

export interface EnabledSiteQuick {
  id: string
  name: string
  logo: string
  url: string
}
