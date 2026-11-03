<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import EmptyState from '@/components/EmptyState.vue'
import { useAuthStore } from '@/stores/auth'
import * as api from '@/api'
import type { KnowledgeBase } from '@/types/api'

const auth = useAuthStore()
const router = useRouter()

const list = ref<KnowledgeBase[]>([])
const loading = ref(true)
const query = ref('')
const showCreate = ref(false)
const createName = ref('')
const createDesc = ref('')
const creating = ref(false)
const createError = ref('')

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return list.value
  return list.value.filter(
    (k) => k.name.toLowerCase().includes(q) || k.description.toLowerCase().includes(q),
  )
})

async function load() {
  loading.value = true
  try {
    list.value = await api.listKnowledgeBases()
  } finally {
    loading.value = false
  }
}

function openKb(id: string) {
  router.push({ name: 'kb-docs', params: { id } })
}

async function submitCreate() {
  createError.value = ''
  if (!createName.value.trim()) {
    createError.value = '请填写知识库名称'
    return
  }
  creating.value = true
  try {
    const kb = await api.createKnowledgeBase({
      name: createName.value,
      description: createDesc.value,
    })
    showCreate.value = false
    createName.value = ''
    createDesc.value = ''
    await load()
    openKb(kb.id)
  } catch (e) {
    createError.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    creating.value = false
  }
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

onMounted(load)
</script>

<template>
  <header class="topbar">
    <h1 class="topbar-title">知识库</h1>
    <div class="topbar-actions">
      <button
        v-if="auth.isAdmin"
        type="button"
        class="btn btn-primary"
        @click="showCreate = true"
      >
        <svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M12 5v14M5 12h14" />
        </svg>
        新建知识库
      </button>
    </div>
  </header>

  <div class="content">
    <div class="content-narrow">
      <div class="page-header">
        <div>
          <h1>知识库列表</h1>
          <p class="page-desc">选择知识库管理文档，或进入对话页提问。</p>
        </div>
      </div>

      <div class="toolbar">
        <div class="search-box">
          <svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.3-4.3" />
          </svg>
          <input v-model="query" class="input" type="search" placeholder="搜索知识库名称或描述" />
        </div>
      </div>

      <div v-if="loading" class="state-panel">
        <div class="spinner" aria-label="加载中" />
        <p class="state-panel-desc">正在加载知识库…</p>
      </div>

      <EmptyState
        v-else-if="list.length === 0"
        title="还没有知识库"
        description="管理员可创建第一个知识库并上传文档，成员即可开始提问。"
      >
        <template #actions>
          <button v-if="auth.isAdmin" type="button" class="btn btn-primary" @click="showCreate = true">
            创建知识库
          </button>
        </template>
      </EmptyState>

      <EmptyState
        v-else-if="filtered.length === 0"
        title="没有匹配的知识库"
        description="试试更换关键词，或清空搜索。"
      />

      <div v-else class="kb-grid">
        <a
          v-for="kb in filtered"
          :key="kb.id"
          class="card kb-card"
          href="#"
          @click.prevent="openKb(kb.id)"
        >
          <div class="kb-card-top">
            <div class="kb-icon" aria-hidden="true">
              <svg class="icon icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
            </div>
            <span class="badge badge-neutral">{{ kb.docCount }} 篇文档</span>
          </div>
          <h2>{{ kb.name }}</h2>
          <p>{{ kb.description }}</p>
          <div class="kb-meta">
            <span>更新 {{ formatDate(kb.updatedAt) }}</span>
            <span>进入</span>
          </div>
        </a>
      </div>
    </div>
  </div>

  <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate = false">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="create-kb-title">
      <h3 id="create-kb-title">新建知识库</h3>
      <p class="modal-desc">填写名称与简要说明，创建后可上传 PDF / Word / Markdown / 文本。</p>
      <div class="field">
        <label class="field-label" for="kb-name">名称</label>
        <input id="kb-name" v-model="createName" class="input" placeholder="例如 人事制度库" />
      </div>
      <div class="field">
        <label class="field-label" for="kb-desc">说明</label>
        <textarea id="kb-desc" v-model="createDesc" class="textarea" placeholder="可选，便于同事识别用途" />
      </div>
      <p v-if="createError" class="field-error">{{ createError }}</p>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" :disabled="creating" @click="showCreate = false">取消</button>
        <button type="button" class="btn btn-primary" :disabled="creating" @click="submitCreate">
          {{ creating ? '创建中…' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>
