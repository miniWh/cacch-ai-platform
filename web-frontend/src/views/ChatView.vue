<script setup lang="ts">
import {computed, nextTick, onMounted, onUnmounted, ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  ChatDotRound,
  Delete,
  Link,
  Plus,
  Position,
  VideoPause,
} from '@element-plus/icons-vue'
import {streamChatCompletions, type ChatCompletionMessage} from '../api/chat'
import {ApiError, request} from '../api/http'
import {ensureDefaultKnowledgeBase} from '../api/kb'
import {listSources} from '../api/sources'
import type {ChatSession, KnowledgeBase, SourceSite} from '../types'

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

function selectSession(id: string) {
  if (sending.value) {
    ElMessage.warning('请等待当前回复完成或先停止生成')
    return
  }
  activeId.value = id
}

async function scrollBottom() {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
}

function createSession() {
  if (sending.value) {
    ElMessage.warning('请等待当前回复完成或先停止生成')
    return
  }
  const id = `s_${Date.now()}`
  sessions.value.unshift({
    id,
    title: '新对话',
    time_label: '刚刚',
    messages: [],
  })
  activeId.value = id
}

async function clearSessions() {
  if (sending.value) stopGeneration()
  await ElMessageBox.confirm('确认清空全部会话记录？', '提示', {
    type: 'warning',
  })
  sessions.value = []
  activeId.value = ''
  ElMessage.success('已清空')
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
  // 控制上下文长度：最近 12 条（不含正在生成的空助手气泡）
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

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  if (!activeSession.value) createSession()
  const session = sessions.value.find((s) => s.id === activeId.value)
  if (!session) return

  const time = nowTime()
  session.messages.push({
    id: `u_${Date.now()}`,
    role: 'user',
    content: text,
    time,
  })
  if (session.title === '新对话') session.title = text.slice(0, 18)
  session.time_label = time
  input.value = ''
  await scrollBottom()

  const assistantId = `a_${Date.now()}`
  session.messages.push({
    id: assistantId,
    role: 'assistant',
    content: '',
    time,
  })
  await scrollBottom()

  sending.value = true
  abortController = new AbortController()
  const assistant = session.messages.find((m) => m.id === assistantId)
  let gotToken = false

  try {
    await streamChatCompletions(
        buildHistoryMessages(session, assistantId),
        {
          onToken: (piece) => {
            gotToken = true
            if (assistant) {
              assistant.content += piece
              void scrollBottom()
            }
          },
          onDone: () => {
            if (assistant && !assistant.content.trim()) {
              assistant.content = '（模型未返回内容）'
            }
          },
          onError: (message) => {
            if (assistant) {
              assistant.content = assistant.content || `调用失败：${message}`
            }
            ElMessage.error(message)
          },
        },
        {signal: abortController.signal},
    )
  } catch (e) {
    if ((e as Error).name === 'AbortError') {
      if (assistant && !gotToken) {
        assistant.content = '（已停止生成）'
      } else if (assistant && gotToken) {
        assistant.content += '\n\n（已停止生成）'
      }
    } else {
      const msg = e instanceof ApiError ? e.message : '请求失败'
      if (assistant && !assistant.content) {
        assistant.content = `调用失败：${msg}`
      }
      ElMessage.error(msg)
    }
  } finally {
    sending.value = false
    abortController = null
    await scrollBottom()
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
  } catch (e) {
    const msg = e instanceof ApiError ? e.message : '加载知识库失败'
    ElMessage.warning(`侧栏信息加载失败：${msg}`)
  }
}

onMounted(() => {
  void bootstrap()
  if (!sessions.value.length) createSession()
})

onUnmounted(() => {
  stopGeneration()
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
          <button
              v-for="s in sessions"
              :key="s.id"
              type="button"
              class="session-item"
              :class="{ active: s.id === activeId }"
              @click="selectSession(s.id)"
          >
            <el-icon>
              <ChatDotRound/>
            </el-icon>
            <div class="meta">
              <div class="title">{{ s.title }}</div>
              <div class="time">{{ s.time_label }}</div>
            </div>
          </button>
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
  gap: 10px;
  align-items: flex-start;
  border: none;
  background: transparent;
  border-radius: 10px;
  padding: 10px;
  text-align: left;
  cursor: pointer;
  color: inherit;
}

.session-item.active,
.session-item:hover {
  background: var(--cacch-primary-muted);
}

.session-item.active {
  outline: 1px solid var(--cacch-primary-soft);
}

.meta .title {
  font-size: 13px;
  font-weight: 600;
}

.meta .time {
  font-size: 12px;
  color: var(--cacch-text-secondary);
  margin-top: 2px;
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
}

.msg-list {
  flex: 1;
  overflow: auto;
  padding: 24px 28px;
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
