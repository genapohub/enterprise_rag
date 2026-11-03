<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import EmptyState from '@/components/EmptyState.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useAuthStore } from '@/stores/auth'
import * as api from '@/api'
import { ApiError } from '@/api'
import type { Member, Role } from '@/types/api'

const auth = useAuthStore()
const list = ref<Member[]>([])
const loading = ref(true)
const query = ref('')
const showInvite = ref(false)
const inviteUsername = ref('')
const inviteName = ref('')
const inviteRole = ref<Role>('member')
const inviting = ref(false)
const inviteError = ref('')

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return list.value
  return list.value.filter(
    (m) =>
      m.displayName.toLowerCase().includes(q) ||
      m.username.toLowerCase().includes(q),
  )
})

const stats = computed(() => {
  const active = list.value.filter((m) => m.status === 'active').length
  const admins = list.value.filter((m) => m.role === 'admin').length
  return { total: list.value.length, active, admins }
})

async function load() {
  loading.value = true
  try {
    list.value = await api.listMembers()
  } finally {
    loading.value = false
  }
}

async function submitInvite() {
  inviteError.value = ''
  if (!inviteUsername.value.trim()) {
    inviteError.value = '请填写账号'
    return
  }
  inviting.value = true
  try {
    await api.inviteMember({
      username: inviteUsername.value,
      displayName: inviteName.value,
      role: inviteRole.value,
    })
    showInvite.value = false
    inviteUsername.value = ''
    inviteName.value = ''
    inviteRole.value = 'member'
    await load()
  } catch (e) {
    inviteError.value = e instanceof ApiError ? e.message : '邀请失败'
  } finally {
    inviting.value = false
  }
}

function initials(name: string) {
  return name.slice(0, 1)
}

onMounted(load)
</script>

<template>
  <header class="topbar">
    <h1 class="topbar-title">成员与角色</h1>
    <div class="topbar-actions">
      <button v-if="auth.isAdmin" type="button" class="btn btn-primary" @click="showInvite = true">
        <svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M19 8v6M22 11h-6" />
        </svg>
        邀请成员
      </button>
    </div>
  </header>

  <div class="content">
    <div class="content-narrow">
      <div class="page-header">
        <div>
          <h1>成员列表</h1>
          <p class="page-desc">管理员可邀请本地账号并分配角色；成员入口对非管理员隐藏。</p>
        </div>
      </div>

      <div class="stats-row">
        <div class="card stat-card">
          <div class="label">成员总数</div>
          <div class="value">{{ stats.total }}</div>
        </div>
        <div class="card stat-card">
          <div class="label">正常</div>
          <div class="value">{{ stats.active }}</div>
        </div>
        <div class="card stat-card">
          <div class="label">管理员</div>
          <div class="value">{{ stats.admins }}</div>
        </div>
      </div>

      <div class="toolbar">
        <div class="search-box">
          <svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.3-4.3" />
          </svg>
          <input v-model="query" class="input" type="search" placeholder="搜索姓名或账号" />
        </div>
      </div>

      <div v-if="loading" class="state-panel">
        <div class="spinner" />
        <p class="state-panel-desc">加载成员…</p>
      </div>

      <EmptyState
        v-else-if="list.length <= 1"
        title="只有你一个人"
        description="邀请同事加入后，他们即可登录并使用已授权知识库。"
      >
        <template #actions>
          <button v-if="auth.isAdmin" type="button" class="btn btn-primary" @click="showInvite = true">邀请成员</button>
        </template>
      </EmptyState>

      <div v-else class="table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>成员</th>
              <th>角色</th>
              <th>状态</th>
              <th>加入日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in filtered" :key="m.id">
              <td>
                <div class="member-cell">
                  <div class="avatar-lg" aria-hidden="true">{{ initials(m.displayName) }}</div>
                  <div>
                    <div class="member-name">{{ m.displayName }}</div>
                    <div class="member-account">{{ m.username }}</div>
                  </div>
                </div>
              </td>
              <td><StatusBadge :status="m.role" /></td>
              <td><StatusBadge :status="m.status" /></td>
              <td>{{ m.joinedAt }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card role-hint">
        <strong>角色说明：</strong>
        管理员可建库、上传/删除文档、邀请成员；成员可查看文档列表并提问，无写操作。
      </div>
    </div>
  </div>

  <div v-if="showInvite" class="modal-backdrop" @click.self="showInvite = false">
    <div class="modal" role="dialog" aria-modal="true">
      <h3>邀请成员</h3>
      <p class="modal-desc">创建本地账号（若后端未开放邀请接口会提示错误；真源见契约）。</p>
      <div class="field">
        <label class="field-label" for="inv-user">账号</label>
        <input id="inv-user" v-model="inviteUsername" class="input" placeholder="例如 wang.fang" />
      </div>
      <div class="field">
        <label class="field-label" for="inv-name">显示名</label>
        <input id="inv-name" v-model="inviteName" class="input" placeholder="例如 王芳" />
      </div>
      <div class="field">
        <label class="field-label" for="inv-role">角色</label>
        <select id="inv-role" v-model="inviteRole" class="select">
          <option value="member">成员</option>
          <option value="admin">管理员</option>
        </select>
      </div>
      <p v-if="inviteError" class="field-error">{{ inviteError }}</p>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" :disabled="inviting" @click="showInvite = false">取消</button>
        <button type="button" class="btn btn-primary" :disabled="inviting" @click="submitInvite">
          {{ inviting ? '提交中…' : '邀请' }}
        </button>
      </div>
    </div>
  </div>
</template>
