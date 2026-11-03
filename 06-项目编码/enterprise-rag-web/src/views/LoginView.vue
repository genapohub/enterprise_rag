<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('admin')
const password = ref('')
const remember = ref(true)
const showPw = ref(false)
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = '请输入账号和密码'
    return
  }
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/knowledge-bases'
    await router.replace(redirect)
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <aside class="login-brand" aria-hidden="true">
      <div class="login-brand-mark">
        <div class="mark">
          <svg class="icon icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            <path d="M8 7h8M8 11h6" />
          </svg>
        </div>
        <div class="name">企业 RAG 知识库</div>
      </div>
      <div class="login-brand-body">
        <h1>用自然语言检索内部文档，答案带来源引用</h1>
        <p>管理员维护知识库与成员；成员选库提问，每条回答附可点击引用，避免无依据的编造。</p>
      </div>
      <div class="login-brand-foot">单组织 · 本地账号 · 内部使用</div>
    </aside>

    <main class="login-panel">
      <div class="login-card">
        <h2>登录</h2>
        <p class="sub">使用本组织下发的账号进入知识库。</p>

        <div v-if="error" class="alert alert-error" role="alert" style="margin-bottom: var(--space-4)">
          <svg class="icon icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
          </svg>
          <div>
            <strong style="display: block; margin-bottom: 2px">无法登录</strong>
            {{ error }}。连续失败请联系管理员重置。
          </div>
        </div>

        <form @submit.prevent="onSubmit">
          <div class="field">
            <label class="field-label" for="username">账号</label>
            <input
              id="username"
              v-model="username"
              class="input"
              :class="{ 'is-error': !!error }"
              type="text"
              autocomplete="username"
              placeholder="例如 admin"
              :disabled="loading"
            />
          </div>
          <div class="field">
            <label class="field-label" for="password">密码</label>
            <div class="password-wrap">
              <input
                id="password"
                v-model="password"
                class="input"
                :class="{ 'is-error': !!error }"
                :type="showPw ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="输入密码"
                :disabled="loading"
              />
              <button type="button" class="toggle-pw" aria-label="显示或隐藏密码" @click="showPw = !showPw">
                <svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
                </svg>
              </button>
            </div>
          </div>
          <div class="login-meta">
            <label class="checkbox">
              <input v-model="remember" type="checkbox" :disabled="loading" />
              在本设备保持登录
            </label>
          </div>
          <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
            <span v-if="loading" class="spinner" style="width: 18px; height: 18px; border-width: 2px" aria-hidden="true" />
            {{ loading ? '登录中…' : '登录' }}
          </button>
        </form>
        <p class="login-foot">联调账号见后端 .env.example：admin / changeme（Mock 开时仍可用 mock 种子）</p>
      </div>
    </main>
  </div>
</template>
