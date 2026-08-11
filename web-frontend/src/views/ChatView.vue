<script setup lang="ts">
import {computed, nextTick, onMounted, onUnmounted, ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  ChatDotRound,
  Delete,
  Link,
  MoreFilled,
  Plus,
  Position,
  VideoPause,
} from '@element-plus/icons-vue'
import {streamChatCompletions, type ChatCompletionMessage} from '../api/chat'
import {ApiError, request} from '../api/http'
import {ensureDefaultKnowledgeBase} from '../api/kb'
import {
  appendMessage,
  clearSessions as clearSessionsApi,
  createSession as createSessionApi,
  deleteSession as deleteSessionApi,
  getSession,
  listSessions,
  updateSession,
} from '../api/sessions'
import {listSources} from '../api/sources'
import type {
  ChatMessage,
  ChatSession,
  ChatSessionApi,
  ChatSessionDetailApi,
  KnowledgeBase,
  SourceSite,
} from '../types'

const sessions = ref<ChatSession[]>([])
const activeId = ref('')
const input = ref('')
const listRef = ref<HTMLElement | null>(null)
const sending = ref(false)
const kb = ref<KnowledgeBase | null>(null)
const activeSites = ref<SourceSite[]>([])
const modelLabel = ref('rag_chat')
let abortController: AbortController | null = null

const activeSession = computed(() => sessions.value.find((s) => s.id === activeId.value))

const siteQuickList = computed(() =>
    activeSites.value
        .filter((s) => s.entry_url)
        .slice(0, 8)
        .map((s) => ({
          id: s.site_id,
          name: s.name,
          logo: s.name.slice(0, 2).toUpperCase(),
          url: s.entry_url as string,
        })),
)

function nowTime() {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now
      .getMinutes()
      .toString()
      .padStart(2, '0')}`
}

function formatTimeLabel(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return nowTime()
  const today = new Date()
  const sameDay =
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth() &&
      d.getDate() === today.getDate()
  const hm = `${d.getHours().toString().padStart(2, '0')}:${d
      .getMinutes()
      .toString()
      .padStart(2, '0')}`
  if (sameDay) return hm
  return `${d.getMonth() + 1}/${d.getDate()} ${hm}`
}

function formatMsgTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return nowTime()
  return `${d.getHours().toString().padStart(2, '0')}:${d
      .getMinutes()
      .toString()
      .padStart(2, '0')}`
}

function mapApiSession(item: ChatSessionApi, messages: ChatMessage[] = []): ChatSession {
  return {
    id: item.session_id,
    title: item.title,
    title_locked: item.title_locked,
    pinned: item.pinned,
    updated_at: item.updated_at,
    time_label: formatTimeLabel(item.updated_at),
    messages,
  }
}

function mapDetail(detail: ChatSessionDetailApi): ChatSession {
  const messages: ChatMessage[] = detail.messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({
        id: m.message_id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        time: formatMsgTime(m.created_at),
        citations: m.citations ?? undefined,
      }))
  return mapApiSession(detail, messages)
}

function sortSessionsLocal() {
  sessions.value.sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
    return b.updated_at.localeCompare(a.updated_at)
  })
}

function applySessionMeta(item: ChatSessionApi) {
  const idx = sessions.value.findIndex((s) => s.id === item.session_id)
  if (idx < 0) return
  const prev = sessions.value[idx]
  sessions.value[idx] = {
    ...prev,
    title: item.title,
    title_locked: item.title_locked,
    pinned: item.pinned,
    updated_at: item.updated_at,
    time_label: formatTimeLabel(item.updated_at),
  }
  sortSessionsLocal()
}

async function selectSession(id: string) {
  if (sending.value) {
    ElMessage.warning('请等待当前回复完成或先停止生成')
    return
  }
  activeId.value = id
  try {
    const detail = await getSession(id)
    const mapped = mapDetail(detail)
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx >= 0) sessions.value[idx] = mapped
    else sessions.value.unshift(mapped)
    sortSessionsLocal()
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '加载会话失败'
    ElMessage.error(msg)
  }
  await nextTick(() => scrollBottom())
}

const bottomAnchorRef = ref<HTMLElement | null>(null)
let scrollRaf = 0

/** 将消息区滚到最新内容底部（布局完成后再滚） */
function scrollBottom(force = true) {
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  scrollRaf = requestAnimationFrame(() => {
    scrollRaf = requestAnimationFrame(() => {
      const list = listRef.value
      const anchor = bottomAnchorRef.value
      if (anchor) {
        anchor.scrollIntoView({block: 'end', behavior: force ? 'auto' : 'smooth'})
      } else if (list) {
        list.scrollTop = list.scrollHeight
      }
      scrollRaf = 0
    })
  })
}

async function createSession() {
  if (sending.value) {
    ElMessage.warning('请等待当前回复完成或先停止生成')
    return
  }
  if (!kb.value) {
    ElMessage.warning('知识库未就绪')
    return
  }
  try {
    const created = await createSessionApi({kb_id: kb.value.id, title: '新对话'})
    const mapped = mapApiSession(created, [])
    sessions.value.unshift(mapped)
    sortSessionsLocal()
    activeId.value = mapped.id
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '创建会话失败'
    ElMessage.error(msg)
  }
}

async function clearSessions() {
  if (!kb.value) return
  if (sending.value) stopGeneration()
  await ElMessageBox.confirm('确认清空全部会话记录？', '提示', {
    type: 'warning',
  })
  try {
    await clearSessionsApi(kb.value.id)
    sessions.value = []
    activeId.value = ''
    ElMessage.success('已清空')
    await createSession()
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '清空失败'
    ElMessage.error(msg)
  }
}

async function renameSession(session: ChatSession) {
  if (sending.value && session.id === activeId.value) {
    ElMessage.warning('请等待当前回复完成或先停止生成')
    return
  }
  try {
    const {value} = await ElMessageBox.prompt('请输入新的会话标题', '重命名', {
      inputValue: session.title,
      inputPattern: /\S+/,
      inputErrorMessage: '标题不能为空',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    const title = value.trim().slice(0, 50)
    const updated = await updateSession(session.id, {title})
    applySessionMeta(updated)
    ElMessage.success('已重命名')
  } catch (e) {
    if (e === 'cancel' || e === 'close') return
    const msg = e instanceof ApiError ? e.message : '重命名失败'
    ElMessage.error(msg)
  }
}

async function togglePinSession(session: ChatSession) {
  try {
    const updated = await updateSession(session.id, {pinned: !session.pinned})
    applySessionMeta(updated)
    ElMessage.success(updated.pinned ? '已置顶' : '已取消置顶')
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '操作失败'
    ElMessage.error(msg)
  }
}

async function removeSession(session: ChatSession) {
  if (sending.value && session.id === activeId.value) {
    ElMessage.warning('请等待当前回复完成或先停止生成')
    return
  }
  await ElMessageBox.confirm(`确认删除会话「${session.title}」？`, '删除会话', {
    type: 'warning',
  })
  try {
    await deleteSessionApi(session.id)
    sessions.value = sessions.value.filter((s) => s.id !== session.id)
    if (activeId.value === session.id) {
      activeId.value = sessions.value[0]?.id ?? ''
      if (activeId.value) await selectSession(activeId.value)
      else await createSession()
    }
    ElMessage.success('已删除')
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '删除失败'
    ElMessage.error(msg)
  }
}

function onSessionMenu(command: string, session: ChatSession) {
  if (command === 'rename') void renameSession(session)
  else if (command === 'pin') void togglePinSession(session)
  else if (command === 'delete') void removeSession(session)
}

function renderMarkdownLite(text: string) {
  return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/^-\s(.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
      .replace(/\n/g, '<br/>')
}

function buildHistoryMessages(
    session: ChatSession,
    excludeMessageId?: string,
): ChatCompletionMessage[] {
  const recent = session.messages
      .filter((m) => m.id !== excludeMessageId && m.content.trim())
      .slice(-12)
  return recent.map((m) => ({
    role: m.role,
    content: m.content,
  }))
}

function stopGeneration() {
  abortController?.abort()
  abortController = null
  sending.value = false
}

async function ensureActiveSession(): Promise<ChatSession | null> {
  if (activeSession.value) return activeSession.value
  await createSession()
  return activeSession.value ?? null
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  const session = await ensureActiveSession()
  if (!session) return

  const time = nowTime()
  const userId = `u_${Date.now()}`
  session.messages.push({
    id: userId,
    role: 'user',
    content: text,
    time,
  })
  if (!session.title_locked && session.title === '新对话') {
    session.title = text.slice(0, 18)
  }
  session.time_label = time
  session.updated_at = new Date().toISOString()
  sortSessionsLocal()
  input.value = ''
  await nextTick()
  scrollBottom()

  try {
    const saved = await appendMessage(session.id, {
      role: 'user',
      content: text,
      message_id: userId,
    })
    // sync title / updated_at from server after auto-title
    const refreshed = await getSession(session.id)
    applySessionMeta(refreshed)
    if (saved.message_id !== userId) {
      const u = session.messages.find((m) => m.id === userId)
      if (u) u.id = saved.message_id
    }
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '保存消息失败'
    ElMessage.warning(msg)
  }

  const assistantId = `a_${Date.now()}`
  session.messages.push({
    id: assistantId,
    role: 'assistant',
    content: '',
    time,
  })
  await nextTick()
  scrollBottom()

  sending.value = true
  abortController = new AbortController()
  const assistantMsgIndex = session.messages.findIndex((m) => m.id === assistantId)
  let gotToken = false

  const patchAssistant = (updater: (prev: string) => string) => {
    if (assistantMsgIndex < 0) return
    const prev = session.messages[assistantMsgIndex]
    session.messages[assistantMsgIndex] = {
      ...prev,
      content: updater(prev.content),
    }
    scrollBottom()
  }

  try {
    await streamChatCompletions(
        buildHistoryMessages(session, assistantId),
        {
          onToken: (piece) => {
            gotToken = true
            patchAssistant((prev) => prev + piece)
          },
          onDone: () => {
            const cur = session.messages[assistantMsgIndex]
            if (cur && !cur.content.trim()) {
              patchAssistant(() => '（模型未返回内容）')
            }
            scrollBottom()
          },
          onError: (message) => {
            patchAssistant((prev) => prev || `调用失败：${message}`)
            ElMessage.error(message)
          },
        },
        {signal: abortController.signal},
    )
  } catch (e) {
    if ((e as Error).name === 'AbortError') {
      if (!gotToken) {
        patchAssistant(() => '（已停止生成）')
      } else {
        patchAssistant((prev) => `${prev}\n\n（已停止生成）`)
      }
    } else {
      const msg = e instanceof ApiError ? e.message : '请求失败'
      patchAssistant((prev) => prev || `调用失败：${msg}`)
      ElMessage.error(msg)
    }
  } finally {
    sending.value = false
    abortController = null
    const finalContent = session.messages[assistantMsgIndex]?.content ?? ''
    if (finalContent.trim()) {
      try {
        await appendMessage(session.id, {
          role: 'assistant',
          content: finalContent,
          message_id: assistantId,
        })
        const refreshed = await getSession(session.id)
        applySessionMeta(refreshed)
      } catch {
        /* ignore persist errors after stream */
      }
    }
    await nextTick()
    scrollBottom()
  }
}

async function loadSessions(kbId: number) {
  const listed = await listSessions(kbId)
  sessions.value = listed.items.map((item) => mapApiSession(item, []))
  sortSessionsLocal()
  if (sessions.value.length) {
    await selectSession(sessions.value[0].id)
  } else {
    await createSession()
  }
}

async function bootstrap() {
  try {
    const kbInfo = await ensureDefaultKnowledgeBase()
    kb.value = kbInfo
    const sources = await listSources(kbInfo.id, {status: 'active'})
    activeSites.value = sources.items
    const profiles = await request<{
      configured: boolean
      items: { alias: string; kind: string; model: string }[]
    }>('/api/v1/core/llm/profiles')
    const rag = profiles.items.find((p) => p.alias === 'rag_chat')
    if (rag?.model) modelLabel.value = rag.model
    await loadSessions(kbInfo.id)
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '加载知识库失败'
    ElMessage.warning(`侧栏信息加载失败：${msg}`)
  }
}

onMounted(() => {
  void bootstrap()
})

onUnmounted(() => {
  stopGeneration()
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
})
</script>

<template>
  <div class="chat-shell">
    <div class="chat-body">
      <aside class="session-pane">
        <div class="session-head">
          <span>会话</span>
        </div>
        <el-button type="primary" class="new-btn" :icon="Plus" @click="createSession">
          新建对话
        </el-button>
        <div class="session-list">
          <div
              v-for="s in sessions"
              :key="s.id"
              class="session-item"
              :class="{ active: s.id === activeId, pinned: s.pinned }"
              @click="selectSession(s.id)"
          >
            <el-icon class="session-icon">
              <ChatDotRound/>
            </el-icon>
            <div class="meta">
              <div class="title-row">
                <span v-if="s.pinned" class="pin-mark" title="已置顶">顶</span>
                <div class="title">{{ s.title }}</div>
              </div>
              <div class="time">{{ s.time_label }}</div>
            </div>
            <el-dropdown
                trigger="click"
                @command="(cmd: string) => onSessionMenu(cmd, s)"
                @click.stop
            >
              <button
                  type="button"
                  class="more-btn"
                  title="更多"
                  @click.stop
              >
                <el-icon><MoreFilled/></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="pin">
                    {{ s.pinned ? '取消置顶' : '置顶' }}
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div v-if="!sessions.length" class="empty">暂无会话</div>
        </div>
        <button type="button" class="clear-btn" @click="clearSessions">
          <el-icon>
            <Delete/>
          </el-icon>
          清空会话记录
        </button>
      </aside>

      <section class="chat-pane">
        <div ref="listRef" class="msg-list">
          <template v-if="activeSession?.messages.length">
            <div
                v-for="m in activeSession.messages"
                :key="m.id"
                class="msg-row"
                :class="m.role"
            >
              <div v-if="m.role === 'assistant'" class="bot-avatar">AI</div>
              <div class="bubble-wrap">
                <div class="bubble" :class="m.role">
                  <div
                      v-if="m.role === 'assistant'"
                      class="assistant-body"
                      v-html="
                      renderMarkdownLite(
                        m.content || (sending && m.id === activeSession.messages.at(-1)?.id ? '思考中…' : ''),
                      )
                    "
                  />
                  <div v-else>{{ m.content }}</div>
                </div>
                <div class="msg-time">{{ m.time }}</div>

                <div v-if="m.citations?.length" class="citations">
                  <div class="cit-title">引用来源</div>
                  <div v-for="c in m.citations" :key="c.index" class="cit-card">
                    <span class="cit-no">{{ c.index }}</span>
                    <div class="cit-body">
                      <div class="cit-name">{{ c.title }}</div>
                      <div class="cit-site">{{ c.site_name }}</div>
                      <a :href="c.url" target="_blank" rel="noreferrer">{{ c.url }}</a>
                      <p class="cit-snip">{{ c.snippet }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="welcome">
            <h2>开始对话</h2>
            <p>
              已对接大模型流式接口。可询问有效成分登记、评审资料等问题；检索增强（RAG
              引用）将在入库流水线就绪后启用。
            </p>
          </div>
          <div ref="bottomAnchorRef" class="msg-list-end" aria-hidden="true"/>
        </div>

        <div class="composer">
          <div class="composer-box">
            <el-input
                v-model="input"
                type="textarea"
                :autosize="{ minRows: 2, maxRows: 6 }"
                :disabled="sending"
                placeholder="询问有效成分登记或评审资料…"
                @keydown.enter.exact.prevent="send"
            />
            <div class="composer-bar">
              <div class="left-hint">{{ sending ? '生成中…' : 'Enter 发送 · Shift+Enter 换行' }}</div>
              <div class="composer-actions">
                <el-button v-if="sending" :icon="VideoPause" @click="stopGeneration">停止</el-button>
                <el-button
                    type="primary"
                    :icon="Position"
                    :loading="sending"
                    :disabled="!input.trim() || sending"
                    @click="send"
                >
                  发送
                </el-button>
              </div>
            </div>
          </div>
          <p class="disclaimer">回答仅供辅助参考，请核对原文</p>
        </div>
      </section>

      <aside class="info-pane">
        <div class="panel">
          <div class="panel-title">当前模块</div>
          <div class="kv">
            <span>能力</span>
            <el-tag size="small" type="success" effect="light">rag_chat</el-tag>
          </div>
          <div class="kv">
            <span>模型档</span>
            <strong>{{ modelLabel }}</strong>
          </div>
          <div class="kv">
            <span>知识库</span>
            <strong>{{ kb?.name || '加载中…' }}</strong>
          </div>
          <div class="kb-card">
            <div class="kb-top">
              <span>知识库 ID {{ kb?.id ?? '—' }}</span>
              <span class="ok">✓</span>
            </div>
            <div class="kb-name">{{ kb?.name || '—' }}</div>
            <div class="kb-sub">
              Embedding：{{ kb?.embedding_model || '—' }} · dim {{ kb?.embedding_dim ?? '—' }}
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title">已启用站点（快捷访问）</div>
          <a
              v-for="site in siteQuickList"
              :key="site.id"
              class="site-card"
              :href="site.url"
              target="_blank"
              rel="noreferrer"
          >
            <span class="logo">{{ site.logo }}</span>
            <div class="site-meta">
              <div class="site-name">{{ site.name }}</div>
              <div class="site-url">{{ site.url }}</div>
            </div>
            <el-icon>
              <Link/>
            </el-icon>
          </a>
          <div v-if="!siteQuickList.length" class="empty">暂无启用站点，请先在站点清单维护</div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.chat-shell {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--cacch-bg);
}

.chat-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 260px;
  align-items: stretch;
}

.chat-body > * {
  min-height: 0;
}

.session-pane {
  background: #fff;
  border-right: 1px solid var(--cacch-border);
  display: flex;
  flex-direction: column;
  padding: 12px;
}

.session-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  margin-bottom: 10px;
}

.new-btn {
  width: 100%;
  margin-bottom: 12px;
}

.session-list {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.session-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  border: none;
  background: transparent;
  border-radius: 10px;
  padding: 10px 8px 10px 10px;
  text-align: left;
  cursor: pointer;
  color: inherit;
  position: relative;
}

.session-item.active,
.session-item:hover {
  background: var(--cacch-primary-muted);
}

.session-item.active {
  outline: 1px solid var(--cacch-primary-soft);
}

.session-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.meta {
  flex: 1;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.pin-mark {
  flex-shrink: 0;
  font-size: 10px;
  line-height: 1;
  padding: 2px 4px;
  border-radius: 3px;
  background: var(--cacch-primary-soft, #d9e8f5);
  color: var(--cacch-primary, #1a6fb5);
  font-weight: 600;
}

.meta .title {
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta .time {
  font-size: 12px;
  color: var(--cacch-text-secondary);
  margin-top: 2px;
}

.more-btn {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--cacch-text-secondary);
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0.55;
  padding: 0;
}

.session-item:hover .more-btn,
.session-item.active .more-btn {
  opacity: 1;
}

.more-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--cacch-text);
}

.clear-btn {
  margin-top: 8px;
  border: none;
  background: transparent;
  color: var(--cacch-text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 8px;
}

.empty,
.welcome {
  color: var(--cacch-text-secondary);
  padding: 24px 8px;
  text-align: center;
  font-size: 13px;
}

.chat-pane {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.msg-list {
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 24px 28px;
  scroll-behavior: auto;
}

.msg-list-end {
  width: 100%;
  height: 1px;
  flex-shrink: 0;
}

.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.msg-row.user {
  justify-content: flex-end;
}

.bot-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--cacch-primary);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.bubble-wrap {
  max-width: min(720px, 85%);
}

.bubble {
  padding: 12px 14px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  background: #fff;
  border: 1px solid var(--cacch-border);
}

.bubble.user {
  background: var(--cacch-user-bubble);
  border-color: transparent;
}

.bubble :deep(ul) {
  margin: 8px 0;
  padding-left: 18px;
}

.msg-time {
  margin-top: 4px;
  font-size: 12px;
  color: var(--cacch-text-secondary);
  text-align: right;
}

.msg-row.assistant .msg-time {
  text-align: left;
}

.citations {
  margin-top: 12px;
}

.cit-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.cit-card {
  display: flex;
  gap: 10px;
  background: #fff;
  border: 1px solid var(--cacch-border);
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.cit-no {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--cacch-primary);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 12px;
  flex-shrink: 0;
}

.cit-name {
  font-weight: 600;
  font-size: 13px;
}

.cit-site {
  font-size: 12px;
  color: var(--cacch-text-secondary);
}

.cit-snip {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--cacch-text-secondary);
}

.composer {
  flex-shrink: 0;
  padding: 0 28px 16px;
}

.composer-box {
  background: #fff;
  border: 1px solid var(--cacch-border);
  border-radius: 14px;
  padding: 10px 12px;
}

.composer-box :deep(.el-textarea__inner) {
  box-shadow: none;
  border: none;
  resize: none;
  padding: 4px;
}

.composer-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  gap: 12px;
}

.left-hint {
  font-size: 12px;
  color: var(--cacch-text-secondary);
}

.composer-actions {
  display: flex;
  gap: 8px;
}

.disclaimer {
  text-align: center;
  font-size: 12px;
  color: var(--cacch-text-secondary);
  margin: 8px 0 0;
}

.info-pane {
  border-left: 1px solid var(--cacch-border);
  background: #fff;
  padding: 16px;
  overflow: auto;
}

.panel {
  margin-bottom: 20px;
}

.panel-title {
  font-weight: 700;
  margin-bottom: 12px;
}

.kv {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 10px;
  color: var(--cacch-text-secondary);
}

.kv strong {
  color: var(--cacch-text);
  font-weight: 600;
  text-align: right;
}

.kb-card,
.site-card {
  border: 1px solid var(--cacch-border);
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

.kb-card {
  margin-top: 8px;
}

.kb-top {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.kb-sub {
  margin-top: 6px;
  font-size: 12px;
  color: var(--cacch-text-secondary);
  word-break: break-all;
}

.ok {
  color: var(--cacch-primary);
  font-weight: 700;
}

.kb-name {
  margin-top: 8px;
  font-weight: 600;
}

.site-card {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
  color: inherit;
}

.logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--cacch-primary-soft);
  color: var(--cacch-primary-dark);
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.site-name {
  font-size: 13px;
  font-weight: 600;
}

.site-url {
  font-size: 11px;
  color: var(--cacch-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

.site-meta {
  flex: 1;
  min-width: 0;
}

.welcome h2 {
  margin: 80px 0 8px;
  text-align: center;
}

@media (max-width: 1100px) {
  .chat-body {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .info-pane {
    display: none;
  }
}
</style>
