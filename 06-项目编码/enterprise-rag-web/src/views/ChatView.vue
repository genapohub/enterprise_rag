<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as api from '@/api'
import { ApiError } from '@/api'
import type { Citation, KnowledgeBase } from '@/types/api'

interface Msg {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  hit?: boolean
  error?: boolean
  questionSnapshot?: string
}

const router = useRouter()
const kbs = ref<KnowledgeBase[]>([])
const kbId = ref('')
const input = ref('')
const messages = ref<Msg[]>([])
const generating = ref(false)
const threadEl = ref<HTMLElement | null>(null)

const suggests = [
  '年假最多可以请几天？',
  '如何申请 VPN？',
  '报销差旅需要哪些票据？',
]

async function loadKbs() {
  kbs.value = await api.listKnowledgeBases()
  if (!kbId.value && kbs.value.length) kbId.value = kbs.value[0].id
}

async function scrollBottom() {
  await nextTick()
  if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight
}

async function send(text?: string) {
  const question = (text ?? input.value).trim()
  if (!question || generating.value) return
  if (!kbId.value) return

  messages.value.push({
    id: `u-${Date.now()}`,
    role: 'user',
    content: question,
  })
  input.value = ''
  generating.value = true
  await scrollBottom()

  try {
    const res = await api.chat({ kbId: kbId.value, question })
    messages.value.push({
      id: `a-${Date.now()}`,
      role: 'assistant',
      content: res.answer,
      citations: res.citations,
      hit: res.hit,
      questionSnapshot: question,
    })
  } catch (e) {
    messages.value.push({
      id: `e-${Date.now()}`,
      role: 'assistant',
      content: e instanceof ApiError ? e.message : '请求失败，请稍后重试',
      error: true,
      questionSnapshot: question,
    })
  } finally {
    generating.value = false
    await scrollBottom()
  }
}

function retry(msg: Msg) {
  if (msg.questionSnapshot) send(msg.questionSnapshot)
}

function openCitation(c: Citation) {
  if (!kbId.value) return
  router.push({ name: 'kb-docs', params: { id: kbId.value }, query: { doc: c.docId } })
}

onMounted(loadKbs)
</script>

<template>
  <header class="topbar">
    <h1 class="topbar-title">对话问答</h1>
  </header>

  <div class="content content-chat">
    <div class="chat-shell">
      <div class="chat-toolbar">
        <label class="sr-only" for="kb-select">选择知识库</label>
        <select id="kb-select" v-model="kbId" class="select kb-select">
          <option disabled value="">选择知识库</option>
          <option v-for="k in kbs" :key="k.id" :value="k.id">{{ k.name }}</option>
        </select>
        <span style="font-size: var(--text-xs); color: var(--color-text-tertiary)">
          答案仅依据所选库中已就绪文档
        </span>
      </div>

      <div ref="threadEl" class="chat-thread">
        <div v-if="messages.length === 0 && !generating" class="empty-chat">
          <div class="state-panel-icon" aria-hidden="true">
            <svg class="icon icon-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <h2>向知识库提问</h2>
          <p>先选择知识库，再输入问题。有依据时答案下方会给出可点击引用；无命中会明确告知未找到。</p>
          <div class="suggest-row">
            <button
              v-for="s in suggests"
              :key="s"
              type="button"
              class="suggest-chip"
              :disabled="!kbId || generating"
              @click="send(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <div v-for="m in messages" :key="m.id" class="msg" :class="m.role === 'user' ? 'msg-user' : 'msg-assistant'">
          <div class="msg-label">{{ m.role === 'user' ? '我' : '助手' }}</div>

          <div v-if="m.error" class="alert alert-error" style="max-width: 720px">
            <div>
              <strong style="display: block; margin-bottom: 4px">请求失败</strong>
              {{ m.content }}
              <div style="margin-top: var(--space-3)">
                <button type="button" class="btn btn-secondary btn-sm" @click="retry(m)">重试</button>
              </div>
            </div>
          </div>

          <div v-else-if="m.role === 'user'" class="bubble bubble-user">{{ m.content }}</div>

          <div v-else class="bubble bubble-assistant">
            <template v-if="m.hit === false">
              <div class="no-hit">
                <strong>{{ m.content || '知识库中未找到相关内容' }}</strong>
                可换一个知识库提问，或请管理员补充相关文档。系统不会编造未收录的内部政策。
              </div>
            </template>
            <template v-else>
              <p>{{ m.content }}</p>
              <div v-if="m.citations?.length" class="cite-list">
                <div class="cite-list-title">引用来源</div>
                <a
                  v-for="(c, idx) in m.citations"
                  :key="idx"
                  class="cite-card"
                  href="#"
                  @click.prevent="openCitation(c)"
                >
                  <div class="cite-doc">{{ c.docName }}</div>
                  <div class="cite-snippet">{{ c.snippet }}</div>
                  <div v-if="c.page" class="cite-meta">约第 {{ c.page }} 页</div>
                </a>
              </div>
            </template>
          </div>
        </div>

        <div v-if="generating" class="msg msg-assistant">
          <div class="msg-label">助手</div>
          <div class="typing" aria-label="生成中">
            <span class="typing-dot" /><span class="typing-dot" /><span class="typing-dot" />
          </div>
        </div>
      </div>

      <div class="composer">
        <div class="composer-box">
          <textarea
            v-model="input"
            rows="1"
            placeholder="输入问题，Enter 发送；Shift+Enter 换行"
            :disabled="generating || !kbId"
            @keydown.enter.exact.prevent="send()"
          />
          <button type="button" class="btn btn-primary" :disabled="generating || !kbId || !input.trim()" @click="send()">
            发送
          </button>
        </div>
        <p class="composer-hint">
          答案与无命中文案以后端为准；引用可点击跳转文档列表。
        </p>
      </div>
    </div>
  </div>
</template>
