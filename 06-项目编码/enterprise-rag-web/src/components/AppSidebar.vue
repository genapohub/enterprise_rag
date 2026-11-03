<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const items = computed(() => {
  const base = [
    { to: '/knowledge-bases', label: '知识库', match: 'knowledge-bases' },
    { to: '/chat', label: '对话问答', match: 'chat' },
  ]
  if (auth.isAdmin) {
    base.push({ to: '/members', label: '成员与角色', match: 'members' })
  }
  return base
})

function isActive(match: string) {
  if (match === 'knowledge-bases') {
    return route.path.startsWith('/knowledge-bases')
  }
  return route.path.startsWith(`/${match}`)
}

const initials = computed(() => {
  const n = auth.user?.displayName || '?'
  return n.slice(0, 1)
})

function onLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <aside class="sidebar" aria-label="主导航">
    <div class="sidebar-brand">
      <div class="sidebar-logo" aria-hidden="true">
        <svg class="icon icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          <path d="M8 7h8M8 11h6" />
        </svg>
      </div>
      <div>
        <div class="sidebar-brand-text">企业 RAG 知识库</div>
        <div class="sidebar-brand-sub">单组织 · 内部</div>
      </div>
    </div>

    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ 'is-active': isActive(item.match) }"
      >
        <svg
          v-if="item.match === 'knowledge-bases'"
          class="icon icon-sm"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          aria-hidden="true"
        >
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
        <svg
          v-else-if="item.match === 'chat'"
          class="icon icon-sm"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          aria-hidden="true"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <svg
          v-else
          class="icon icon-sm"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          aria-hidden="true"
        >
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <div class="user-chip">
        <div class="avatar" aria-hidden="true">{{ initials }}</div>
        <div style="min-width: 0; flex: 1">
          <div class="user-name">{{ auth.user?.displayName }}</div>
          <div class="user-role">{{ auth.isAdmin ? '管理员' : '成员' }}</div>
        </div>
        <button type="button" class="btn btn-ghost btn-sm" style="color: var(--color-text-sidebar)" @click="onLogout">
          退出
        </button>
      </div>
    </div>
  </aside>
</template>
