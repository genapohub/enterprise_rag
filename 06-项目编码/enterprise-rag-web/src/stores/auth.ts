import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { User } from '@/types/api'
import * as api from '@/api'
import { setAccessToken } from '@/api/http'

const TOKEN_KEY = 'enterprise-rag.token'
const USER_KEY = 'enterprise-rag.user'

function readUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(readUser())

  const isAuthenticated = computed(() => Boolean(token.value && user.value))
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const res = await api.login({ username, password })
    token.value = res.accessToken
    user.value = res.user
    setAccessToken(res.accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(res.user))
  }

  async function refreshMe() {
    const me = await api.fetchMe()
    user.value = me
    localStorage.setItem(USER_KEY, JSON.stringify(me))
  }

  function logout() {
    token.value = null
    user.value = null
    setAccessToken(null)
    localStorage.removeItem(USER_KEY)
  }

  return { token, user, isAuthenticated, isAdmin, login, logout, refreshMe }
})
