<script setup lang="ts">
import { computed } from 'vue'
import type { DocStatus, Role } from '@/types/api'

const props = defineProps<{
  status: DocStatus | Role | 'active' | 'disabled'
}>()

const label = computed(() => {
  const map: Record<string, string> = {
    uploaded: '已上传',
    parsing: '解析中',
    chunking: '切块中',
    indexing: '索引中',
    ready: '已就绪',
    parse_failed: '解析失败',
    index_failed: '索引失败',
    active: '正常',
    disabled: '已停用',
    admin: '管理员',
    member: '成员',
  }
  return map[props.status] || props.status
})

const klass = computed(() => {
  const map: Record<string, string> = {
    uploaded: 'badge-pending',
    parsing: 'badge-indexing',
    chunking: 'badge-indexing',
    indexing: 'badge-indexing',
    ready: 'badge-ready',
    parse_failed: 'badge-failed',
    index_failed: 'badge-failed',
    active: 'badge-ready',
    disabled: 'badge-neutral',
    admin: 'badge-admin',
    member: 'badge-member',
  }
  return map[props.status] || 'badge-neutral'
})
</script>

<template>
  <span class="badge badge-dot" :class="klass">{{ label }}</span>
</template>
