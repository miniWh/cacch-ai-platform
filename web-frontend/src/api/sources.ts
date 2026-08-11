import { request } from './http'
import type {
  CrawlMode,
  RegionCode,
  SiteCategory,
  SiteStatus,
  SourceSite,
} from '../types'

export interface SourceListQuery {
  keyword?: string
  region?: string
  category?: string
  status?: string
}

export interface SourceSiteCreatePayload {
  site_id: string
  name: string
  region: RegionCode
  category: SiteCategory
  entry_url?: string | null
  crawl_mode: CrawlMode
  allowed_domains?: string[]
  status?: SiteStatus
  notes?: string | null
}

export interface SourceSiteUpdatePayload {
  name?: string
  region?: RegionCode
  category?: SiteCategory
  entry_url?: string | null
  crawl_mode?: CrawlMode
  allowed_domains?: string[]
  status?: SiteStatus
  notes?: string | null
}

export async function listSources(
  kbId: number,
  query: SourceListQuery = {},
): Promise<{ items: SourceSite[]; total: number }> {
  const params = new URLSearchParams()
  if (query.keyword) params.set('keyword', query.keyword)
  if (query.region) params.set('region', query.region)
  if (query.category) params.set('category', query.category)
  if (query.status) params.set('status', query.status)
  const qs = params.toString()
  return request(`/api/v1/rag/kb/${kbId}/sources${qs ? `?${qs}` : ''}`)
}

export async function createSource(
  kbId: number,
  payload: SourceSiteCreatePayload,
): Promise<SourceSite> {
  return request(`/api/v1/rag/kb/${kbId}/sources`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateSource(
  kbId: number,
  siteId: string,
  payload: SourceSiteUpdatePayload,
): Promise<SourceSite> {
  return request(`/api/v1/rag/kb/${kbId}/sources/${encodeURIComponent(siteId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteSource(kbId: number, siteId: string): Promise<void> {
  await request(`/api/v1/rag/kb/${kbId}/sources/${encodeURIComponent(siteId)}`, {
    method: 'DELETE',
  })
}

export async function probeSources(
  kbId: number,
  siteIds?: string[],
): Promise<{
  results: Array<{
    site_id: string
    name: string
    status: string
    last_probe_status: string | null
    last_probe_at: string | null
  }>
}> {
  return request(`/api/v1/rag/kb/${kbId}/sources/probe`, {
    method: 'POST',
    body: JSON.stringify(siteIds ? { site_ids: siteIds } : {}),
  })
}
