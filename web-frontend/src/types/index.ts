export type RegionCode = 'US' | 'EU' | 'UK' | 'AU' | 'JP' | 'CN' | 'INT'
export type SiteCategory = 'registration' | 'evaluation' | 'standard' | 'database'
export type CrawlMode = 'manual' | 'single_page' | 'list_harvest' | 'connector'
export type SiteStatus = 'active' | 'broken' | 'pending_url' | 'disabled'

export interface SourceSite {
  site_id: string
  name: string
  region: RegionCode
  category: SiteCategory
  entry_url: string
  crawl_mode: CrawlMode
  allowed_domains: string[]
  status: SiteStatus
  notes: string
  last_probe_at: string | null
  last_probe_status: string | null
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

export interface ChatSession {
  id: string
  title: string
  time_label: string
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
