<script setup lang="ts">
import AppSidebar from '@/components/AppSidebar.vue'
</script>

<template>
  <div class="app-shell">
    <AppSidebar />
    <div class="main">
      <RouterView />
    </div>
  </div>
</template>
