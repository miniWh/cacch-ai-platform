import {API_AUTH_TOKEN, API_BASE_URL} from '../config'
import {ApiError} from './http'

export type ChatRole = 'system' | 'user' | 'assistant'

export interface ChatCompletionMessage {
    role: ChatRole
    content: string
}

export interface ChatStreamHandlers {
    onToken: (text: string) => void
    onDone?: (meta: { request_id?: string; profile_id?: string }) => void
    onError?: (message: string) => void
}

/** SSE 流式对话（对接 POST /api/v1/core/llm/chat/completions?stream） */
export async function streamChatCompletions(
    messages: ChatCompletionMessage[],
    handlers: ChatStreamHandlers,
    options?: {
        profileId?: string
        signal?: AbortSignal
    },
): Promise<void> {
    const headers = new Headers({
        Authorization: `Bearer ${API_AUTH_TOKEN}`,
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
    })

    const res = await fetch(`${API_BASE_URL}/api/v1/core/llm/chat/completions`, {
        method: 'POST',
        headers,
        signal: options?.signal,
        body: JSON.stringify({
            messages,
            profile_id: options?.profileId || 'rag_chat',
            stream: true,
        }),
    })

    if (res.status === 401) {
        throw new ApiError(401, '未授权')
    }
    if (!res.ok) {
        let message = `请求失败（HTTP ${res.status}）`
        try {
            const payload = (await res.json()) as { message?: string }
            if (payload.message) message = payload.message
        } catch {
            /* ignore */
        }
        throw new ApiError(res.status, message)
    }

    if (!res.body) {
        throw new ApiError(502, '响应无正文')
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
        const {done, value} = await reader.read()
        if (done) break
        buffer += decoder.decode(value, {stream: true})
        const parts = buffer.split('\n')
        buffer = parts.pop() || ''

        for (const line of parts) {
            const trimmed = line.trim()
            if (!trimmed || trimmed.startsWith(':')) continue
            if (!trimmed.startsWith('data:')) continue
            const dataStr = trimmed.slice(5).trim()
            if (!dataStr || dataStr === '[DONE]') continue
            let event: {
                type?: string
                content?: string
                message?: string
                request_id?: string
                profile_id?: string
            }
            try {
                event = JSON.parse(dataStr) as typeof event
            } catch {
                continue
            }
            if (event.type === 'token' && event.content) {
                handlers.onToken(event.content)
            } else if (event.type === 'done') {
                handlers.onDone?.({
                    request_id: event.request_id,
                    profile_id: event.profile_id,
                })
            } else if (event.type === 'error') {
                handlers.onError?.(event.message || '模型调用失败')
            }
        }
    }
}
