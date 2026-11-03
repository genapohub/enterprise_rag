/**
 * API facade: default = real backend; VITE_USE_MOCK=true keeps local mock.
 */
import type { User } from '@/types/api'
import * as mock from '@/mock/api'
import * as real from './client'
import { ApiError } from './http'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'
const impl = useMock ? mock : real

export { ApiError }

export const login = impl.login
export const listKnowledgeBases = impl.listKnowledgeBases
export const createKnowledgeBase = impl.createKnowledgeBase
export const getKnowledgeBase = impl.getKnowledgeBase
export const listDocuments = impl.listDocuments
export const uploadDocument = impl.uploadDocument
export const deleteDocument = impl.deleteDocument
export const chat = impl.chat
export const listMembers = impl.listMembers
export const inviteMember = impl.inviteMember

/** Real-only helpers (mock reads cached user). */
export async function fetchMe(): Promise<User> {
  if (useMock) {
    try {
      const raw = localStorage.getItem('enterprise-rag.user')
      if (!raw) throw new ApiError(401, '未登录')
      return JSON.parse(raw) as User
    } catch (e) {
      if (e instanceof ApiError) throw e
      throw new ApiError(401, '未登录')
    }
  }
  return real.fetchMe()
}

export async function reindexDocument(docId: string) {
  if (useMock) {
    throw new ApiError(501, 'Mock 未实现重试索引；请关闭 VITE_USE_MOCK 接真后端')
  }
  return real.reindexDocument(docId)
}

export const isMockMode = useMock
