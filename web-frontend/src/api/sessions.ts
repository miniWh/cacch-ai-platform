import { request } from './http'
import type { ChatSessionApi, ChatSessionDetailApi } from '../types'

export async function listSessions(kbId: number): Promise<{
  items: ChatSessionApi[]
  total: number
}> {
  return request(`/api/v1/rag/sessions?kb_id=${kbId}`)
}

export async function createSession(payload: {
  kb_id: number
  title?: string
}): Promise<ChatSessionApi> {
  return request('/api/v1/rag/sessions', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getSession(sessionId: string): Promise<ChatSessionDetailApi> {
  return request(`/api/v1/rag/sessions/${encodeURIComponent(sessionId)}`)
}

export async function updateSession(
  sessionId: string,
  payload: { title?: string; pinned?: boolean },
): Promise<ChatSessionApi> {
  return request(`/api/v1/rag/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteSession(sessionId: string): Promise<{ session_id: string }> {
  return request(`/api/v1/rag/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  })
}

export async function clearSessions(kbId: number): Promise<{ deleted: number }> {
  return request(`/api/v1/rag/sessions?kb_id=${kbId}`, {
    method: 'DELETE',
  })
}

export async function appendMessage(
  sessionId: string,
  payload: {
    role: 'user' | 'assistant' | 'system'
    content: string
    message_id?: string
    citations?: unknown[]
  },
): Promise<{
  message_id: string
  session_id: string
  role: string
  content: string
  created_at: string
}> {
  return request(`/api/v1/rag/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
