import { request } from './http'
import type { KnowledgeBase } from '../types'

export async function listKnowledgeBases(): Promise<{
  items: KnowledgeBase[]
  total: number
}> {
  return request('/api/v1/rag/kb')
}

export async function ensureDefaultKnowledgeBase(): Promise<KnowledgeBase> {
  return request('/api/v1/rag/kb/ensure-default', { method: 'POST' })
}
