<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  Delete,
  Document,
  Link,
  Paperclip,
  Plus,
  Position,
} from '@element-plus/icons-vue'
import { currentApp, enabledSitesQuick, mockSessions } from '../mock/data'
import type { ChatSession } from '../types'

const sessions = ref<ChatSession[]>(structuredClone(mockSessions))
const activeId = ref(sessions.value[0]?.id || '')
const input = ref('')
const listRef = ref<HTMLElement | null>(null)

const activeSession = computed(() => sessions.value.find((s) => s.id === activeId.value))

function selectSession(id: string) {
  activeId.value = id
}

async function scrollBottom() {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
}

function createSession() {
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
  await ElMessageBox.confirm('确认清空全部会话记录？（仅前端测试数据）', '提示', {
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

function mockReply(question: string) {
  const lower = question.toLowerCase()
  if (lower.includes('没有') || lower.includes('未知物质xyz')) {
    return {
      content:
        '未在当前知识库命中相关片段。建议：1）核对有效成分中英文名；2）从右侧已启用站点进入官网检索；3）由管理员在站点清单维护后同步入库。\n\n本回答仅供辅助参考，不构成法规符合性认定。',
      citations: [],
    }
  }
  return {
    content: `已根据测试知识库对「${question}」生成示意回答。\n\n**检索摘要**\n- 命中若干与有效成分登记/评审相关的片段\n- 请结合下方引用来源打开原文核对\n\n**说明**\n- 当前为前端 Mock 数据，尚未对接真实 RAG 接口`,
    citations: [
      {
        index: 1,
        title: '示意引用 · 农药登记评审资料片段',
        site_name: '农药登记评审资料',
        url: 'https://www.efsa.europa.eu/en/publications',
        snippet: '…（测试）与提问相关的上下文片段将显示在此处…',
      },
    ],
  }
}

async function send() {
  const text = input.value.trim()
  if (!text) return
  if (!activeSession.value) createSession()
  const session = sessions.value.find((s) => s.id === activeId.value)
  if (!session) return

  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now
    .getMinutes()
    .toString()
    .padStart(2, '0')}`

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

  const reply = mockReply(text)
  session.messages.push({
    id: `a_${Date.now()}`,
    role: 'assistant',
    content: reply.content,
    time,
    citations: reply.citations,
  })
  await scrollBottom()
}
</script>

<template>
  <div class="chat-shell">
    <div class="chat-body">
      <aside class="session-pane">
        <div class="session-head">
          <span>会话</span>
        </div>
        <el-button type="primary" class="new-btn" :icon="Plus" @click="createSession">新建对话</el-button>
        <div class="session-list">
          <button
            v-for="s in sessions"
            :key="s.id"
            type="button"
            class="session-item"
            :class="{ active: s.id === activeId }"
            @click="selectSession(s.id)"
          >
            <el-icon><ChatDotRound /></el-icon>
            <div class="meta">
              <div class="title">{{ s.title }}</div>
              <div class="time">{{ s.time_label }}</div>
            </div>
          </button>
          <div v-if="!sessions.length" class="empty">暂无会话</div>
        </div>
        <button type="button" class="clear-btn" @click="clearSessions">
          <el-icon><Delete /></el-icon>
          清空会话记录
        </button>
      </aside>

      <!-- messages -->
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
                  <div v-if="m.role === 'assistant'" v-html="renderMarkdownLite(m.content)" />
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
            <h2>农药登记评审资料问答</h2>
            <p>可询问有效成分在各国的登记情况或评审资料。当前为前端 Mock 演示。</p>
          </div>
        </div>

        <div class="composer">
          <div class="composer-box">
            <el-input
              v-model="input"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 6 }"
              placeholder="询问有效成分登记或评审资料…"
              @keydown.enter.exact.prevent="send"
            />
            <div class="composer-bar">
              <div class="left-icons">
                <el-icon><Paperclip /></el-icon>
                <el-icon><Document /></el-icon>
              </div>
              <el-button type="primary" :icon="Position" @click="send">发送</el-button>
            </div>
          </div>
          <p class="disclaimer">回答仅供辅助参考，请核对原文</p>
        </div>
      </section>

      <!-- right app panel -->
      <aside class="info-pane">
        <div class="panel">
          <div class="panel-title">当前 App</div>
          <div class="kv">
            <span>app_type</span>
            <el-tag size="small" type="success" effect="light">{{ currentApp.app_type }}</el-tag>
          </div>
          <div class="kv">
            <span>应用名称</span>
            <strong>{{ currentApp.name }}</strong>
          </div>
          <div class="kv">
            <span>知识库</span>
            <strong>{{ currentApp.kb_name }}</strong>
          </div>
          <div class="kb-card">
            <div class="kb-top">
              <span>已绑定 {{ currentApp.kb_count }} 个知识库</span>
              <span class="ok">✓</span>
            </div>
            <div class="kb-name">{{ currentApp.kb_name }}</div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title">已启用站点（快捷访问）</div>
          <a
            v-for="site in enabledSitesQuick"
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
            <el-icon><Link /></el-icon>
          </a>
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
}

.left-icons {
  display: flex;
  gap: 12px;
  color: var(--cacch-text-secondary);
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
