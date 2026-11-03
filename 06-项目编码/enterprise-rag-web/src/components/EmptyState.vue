<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="state-panel">
    <div class="state-panel-icon" aria-hidden="true">
      <slot name="icon">
        <svg class="icon icon-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
      </slot>
    </div>
    <h2 class="state-panel-title">{{ title }}</h2>
    <p v-if="description" class="state-panel-desc">{{ description }}</p>
    <div v-if="$slots.actions" class="state-panel-actions">
      <slot name="actions" />
    </div>
  </div>
</template>
