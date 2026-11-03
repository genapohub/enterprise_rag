<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '@/components/EmptyState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useAuthStore } from '@/stores/auth'
import * as api from '@/api'
import { ApiError } from '@/api'
import type { DocumentItem, KnowledgeBase } from '@/types/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const kbId = computed(() => String(route.params.id || ''))
const kb = ref<KnowledgeBase | null>(null)
const docs = ref<DocumentItem[]>([])
const loading = ref(true)
const error = ref('')
const uploadError = ref('')
const uploading = ref(false)
const dragOver = ref(false)
const pendingDelete = ref<DocumentItem | null>(null)
const deleting = ref(false)
const reindexingId = ref<string | null>(null)
let pollTimer: number | undefined

async function onReindex(doc: DocumentItem) {
  if (!auth.isAdmin) return
  reindexingId.value = doc.id
  uploadError.value = ''
  try {
    await api.reindexDocument(doc.id)
    await refreshDocs()
  } catch (e) {
    uploadError.value = e instanceof ApiError ? e.message : '重试失败'
  } finally {
    reindexingId.value = null
  }
}

function canReindex(status: DocumentItem['status']) {
  return status === 'parse_failed' || status === 'index_failed'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    kb.value = await api.getKnowledgeBase(kbId.value)
    docs.value = await api.listDocuments(kbId.value)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '加载失败'
    docs.value = []
  } finally {
    loading.value = false
  }
}

async function refreshDocs() {
  try {
    docs.value = await api.listDocuments(kbId.value)
    if (kb.value) {
      kb.value = await api.getKnowledgeBase(kbId.value)
    }
  } catch {
    /* ignore poll errors */
  }
}

async function onFiles(fileList: FileList | null) {
  if (!auth.isAdmin || !fileList?.length) return
  uploadError.value = ''
  uploading.value = true
  try {
    for (const file of Array.from(fileList)) {
      await api.uploadDocument(kbId.value, file)
    }
    await refreshDocs()
  } catch (e) {
    uploadError.value = e instanceof ApiError ? e.message : '上传失败'
  } finally {
    uploading.value = false
  }
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  onFiles(e.dataTransfer?.files || null)
}

async function confirmDelete() {
  if (!pendingDelete.value) return
  deleting.value = true
  try {
    await api.deleteDocument(kbId.value, pendingDelete.value.id)
    pendingDelete.value = null
    await refreshDocs()
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    deleting.value = false
  }
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

watch(kbId, () => load())

onMounted(() => {
  load()
  pollTimer = window.setInterval(() => {
    if (
      docs.value.some((d) =>
        ['uploaded', 'parsing', 'chunking', 'indexing'].includes(d.status),
      )
    ) {
      refreshDocs()
    }
  }, 1500)
})

onUnmounted(() => {
  if (pollTimer) window.clearInterval(pollTimer)
})
</script>

<template>
  <header class="topbar">
    <h1 class="topbar-title">文档管理</h1>
    <div class="topbar-actions">
      <button type="button" class="btn btn-secondary" @click="router.push({ name: 'knowledge-bases' })">
        返回列表
      </button>
    </div>
  </header>

  <div class="content">
    <div class="content-narrow">
      <nav class="crumb" aria-label="面包屑">
        <RouterLink to="/knowledge-bases">知识库</RouterLink>
        <span class="crumb-sep">/</span>
        <span>{{ kb?.name || '…' }}</span>
      </nav>

      <div class="page-header">
        <div>
          <h1>{{ kb?.name || '文档管理' }}</h1>
          <p class="page-desc">上传文档后查看解析与索引状态；删除后后续问答不再引用该文档。</p>
        </div>
      </div>

      <div v-if="uploadError" class="alert alert-error" role="alert" style="margin-bottom: var(--space-4)">
        <svg class="icon icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
        </svg>
        <div>{{ uploadError }}</div>
      </div>

      <div
        v-if="auth.isAdmin"
        class="upload-zone"
        :class="{ 'is-drag': dragOver }"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
      >
        <svg class="icon icon-xl" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true" style="color: var(--color-accent); margin: 0 auto">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <h3>{{ uploading ? '上传中…' : '拖拽文件到此处，或选择上传' }}</h3>
        <p>支持 PDF、Word（.docx）、Markdown、纯文本</p>
        <label class="btn btn-primary">
          选择文件
          <input
            class="sr-only"
            type="file"
            multiple
            accept=".pdf,.docx,.md,.txt,application/pdf,text/markdown,text/plain"
            :disabled="uploading"
            @change="onFiles(($event.target as HTMLInputElement).files); ($event.target as HTMLInputElement).value = ''"
          />
        </label>
      </div>

      <div v-if="loading" class="table-wrap">
        <table class="data">
          <thead>
            <tr><th>文档</th><th>状态</th><th>更新时间</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="i in 3" :key="i" class="skeleton-row">
              <td><div class="skel" style="width: 60%" /></td>
              <td><div class="skel" style="width: 80px" /></td>
              <td><div class="skel" style="width: 120px" /></td>
              <td />
            </tr>
          </tbody>
        </table>
      </div>

      <EmptyState
        v-else-if="error"
        title="无法加载文档列表"
        :description="error"
      >
        <template #icon>
          <svg class="icon icon-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
          </svg>
        </template>
        <template #actions>
          <button type="button" class="btn btn-primary" @click="load">重试</button>
        </template>
      </EmptyState>

      <EmptyState
        v-else-if="docs.length === 0"
        title="知识库还没有文档"
        description="上传 PDF、Word、Markdown 或文本后，即可在对话页基于本库提问。"
      />

      <div v-else class="table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>文档</th>
              <th>状态</th>
              <th>更新时间</th>
              <th style="text-align: right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in docs" :key="doc.id">
              <td>
                <div class="doc-name">
                  <div class="doc-file-icon" aria-hidden="true">
                    <svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </div>
                  <div>
                    <div>{{ doc.name }}</div>
                    <div class="doc-sub">{{ doc.format.toUpperCase() }} · {{ doc.sizeLabel }}</div>
                    <div v-if="doc.statusReason" class="doc-sub" style="color: var(--color-danger)">{{ doc.statusReason }}</div>
                  </div>
                </div>
              </td>
              <td><StatusBadge :status="doc.status" /></td>
              <td>{{ formatDate(doc.updatedAt) }}</td>
              <td>
                <div class="row-actions">
                  <button
                    v-if="auth.isAdmin && canReindex(doc.status)"
                    type="button"
                    class="btn btn-secondary btn-sm"
                    :disabled="reindexingId === doc.id"
                    @click="onReindex(doc)"
                  >
                    {{ reindexingId === doc.id ? '重试中…' : '重试索引' }}
                  </button>
                  <button
                    v-if="auth.isAdmin"
                    type="button"
                    class="btn btn-danger-outline btn-sm"
                    @click="pendingDelete = doc"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="!auth.isAdmin" class="member-note">当前为成员账号：可查看文档列表，不可上传或删除。</p>
    </div>
  </div>

  <div v-if="pendingDelete" class="modal-backdrop" @click.self="pendingDelete = null">
    <div class="modal confirm-box" role="dialog" aria-modal="true">
      <h3>确认删除文档？</h3>
      <p>
        将删除「{{ pendingDelete.name }}」。删除后后续问答不再引用该文档；不会回溯改写历史回答。
      </p>
      <div class="confirm-actions">
        <button type="button" class="btn btn-secondary" :disabled="deleting" @click="pendingDelete = null">取消</button>
        <button type="button" class="btn btn-danger" :disabled="deleting" @click="confirmDelete">
          {{ deleting ? '删除中…' : '确认删除' }}
        </button>
      </div>
    </div>
  </div>
</template>
