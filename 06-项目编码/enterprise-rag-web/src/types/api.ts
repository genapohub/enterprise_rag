/** API shapes aligned with 企业RAG_API契约_v0.1 (camelCase at UI boundary). */

export type Role = 'admin' | 'member'

/** Document status machine (contract §1). */
export type DocStatus =
  | 'uploaded'
  | 'parsing'
  | 'chunking'
  | 'indexing'
  | 'ready'
  | 'parse_failed'
  | 'index_failed'

export interface User {
  id: string
  username: string
  displayName: string
  role: Role
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken?: string
  user: User
}

export interface KnowledgeBase {
  id: string
  name: string
  description: string
  docCount: number
  updatedAt: string
  archived?: boolean
}

export interface DocumentItem {
  id: string
  kbId: string
  name: string
  format: string
  sizeLabel: string
  status: DocStatus
  statusReason?: string
  updatedAt: string
}

export interface Citation {
  docId: string
  docName: string
  snippet: string
  page?: number
  score?: number
  chunkId?: string
}

export interface ChatRequest {
  kbId: string
  question: string
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  hit: boolean
}

export interface Member {
  id: string
  username: string
  displayName: string
  role: Role
  status: 'active' | 'disabled'
  joinedAt: string
}

export interface InviteMemberRequest {
  username: string
  displayName: string
  role: Role
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
