/**
 * Real backend client — paths under /api/v1, maps snake_case → camelCase for UI.
 */
import type {
  ChatRequest,
  ChatResponse,
  Citation,
  DocumentItem,
  InviteMemberRequest,
  KnowledgeBase,
  LoginRequest,
  LoginResponse,
  Member,
  PageResult,
  User,
} from '@/types/api'
import { ApiError, request, requestForm } from './http'

const PREFIX = '/api/v1'

interface SnakeUser {
  id: string
  username: string
  display_name: string
  role: 'admin' | 'member'
}

interface SnakeLogin {
  access_token: string
  refresh_token?: string
  token_type?: string
  expires_in?: number
  user: SnakeUser
}

interface SnakeKb {
  id: string
  name: string
  description?: string | null
  is_archived?: boolean
  doc_count?: number
  created_at?: string
  updated_at?: string
}

interface SnakeDoc {
  id: string
  kb_id: string
  name: string
  content_type?: string | null
  size_bytes?: number
  status: DocumentItem['status']
  fail_reason?: string | null
  is_archived?: boolean
  chunk_count?: number
  created_at?: string
  updated_at?: string
  indexed_at?: string | null
}

interface SnakeCitation {
  doc_id: string
  doc_name: string
  chunk_id: string
  snippet: string
  page?: number | null
  score?: number | null
}

interface SnakeMember {
  id: string
  username: string
  display_name: string
  role: 'admin' | 'member'
  is_active: boolean
  created_at?: string
}

interface SnakeConversation {
  id: string
  kb_id: string
  title?: string | null
}

interface SnakeChatData {
  user_message: { id: string; role: string; content: string; created_at?: string }
  assistant_message: {
    id: string
    role: string
    content: string
    citations: SnakeCitation[]
    created_at?: string
  }
}

function mapUser(u: SnakeUser): User {
  return {
    id: u.id,
    username: u.username,
    displayName: u.display_name,
    role: u.role,
  }
}

function mapKb(k: SnakeKb): KnowledgeBase {
  return {
    id: k.id,
    name: k.name,
    description: k.description || '',
    docCount: k.doc_count ?? 0,
    updatedAt: k.updated_at || k.created_at || new Date().toISOString(),
    archived: Boolean(k.is_archived),
  }
}

function formatSize(bytes?: number): string {
  if (bytes == null || Number.isNaN(bytes)) return '—'
  if (bytes > 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${Math.max(1, Math.round(bytes / 1024))} KB`
}

function guessFormat(name: string, contentType?: string | null): string {
  const ext = name.split('.').pop()?.toLowerCase()
  if (ext) return ext
  if (contentType?.includes('pdf')) return 'pdf'
  if (contentType?.includes('word')) return 'docx'
  if (contentType?.includes('markdown')) return 'md'
  return 'txt'
}

function mapDoc(d: SnakeDoc): DocumentItem {
  return {
    id: d.id,
    kbId: d.kb_id,
    name: d.name,
    format: guessFormat(d.name, d.content_type),
    sizeLabel: formatSize(d.size_bytes),
    status: d.status,
    statusReason: d.fail_reason || undefined,
    updatedAt: d.updated_at || d.created_at || new Date().toISOString(),
  }
}

function mapCitation(c: SnakeCitation): Citation {
  return {
    docId: c.doc_id,
    docName: c.doc_name,
    snippet: c.snippet,
    page: c.page ?? undefined,
    score: c.score ?? undefined,
    chunkId: c.chunk_id,
  }
}

function mapMember(m: SnakeMember): Member {
  const joined = m.created_at ? m.created_at.slice(0, 10) : ''
  return {
    id: m.id,
    username: m.username,
    displayName: m.display_name,
    role: m.role,
    status: m.is_active ? 'active' : 'disabled',
    joinedAt: joined,
  }
}

/** In-memory conversation id per knowledge base for this session. */
const conversationByKb = new Map<string, string>()

export async function login(body: LoginRequest): Promise<LoginResponse> {
  const data = await request<SnakeLogin>(`${PREFIX}/auth/login`, {
    method: 'POST',
    auth: false,
    body: { username: body.username, password: body.password },
  })
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    user: mapUser(data.user),
  }
}

export async function fetchMe(): Promise<User> {
  const data = await request<SnakeUser>(`${PREFIX}/auth/me`)
  return mapUser(data)
}

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  const data = await request<PageResult<SnakeKb> | SnakeKb[]>(`${PREFIX}/knowledge-bases`)
  const items = Array.isArray(data) ? data : data.items || []
  return items.filter((k) => !k.is_archived).map(mapKb)
}

export async function createKnowledgeBase(input: {
  name: string
  description?: string
}): Promise<KnowledgeBase> {
  const data = await request<SnakeKb>(`${PREFIX}/knowledge-bases`, {
    method: 'POST',
    body: { name: input.name.trim(), description: (input.description || '').trim() },
  })
  return mapKb(data)
}

export async function getKnowledgeBase(id: string): Promise<KnowledgeBase> {
  const data = await request<SnakeKb>(`${PREFIX}/knowledge-bases/${id}`)
  return mapKb(data)
}

export async function listDocuments(kbId: string): Promise<DocumentItem[]> {
  const data = await request<PageResult<SnakeDoc> | SnakeDoc[]>(
    `${PREFIX}/knowledge-bases/${kbId}/documents`,
  )
  const items = Array.isArray(data) ? data : data.items || []
  return items.map(mapDoc)
}

export async function uploadDocument(kbId: string, file: File): Promise<DocumentItem> {
  const form = new FormData()
  form.append('file', file)
  const data = await requestForm<SnakeDoc>(`${PREFIX}/knowledge-bases/${kbId}/documents`, form)
  return mapDoc(data)
}

export async function deleteDocument(_kbId: string, docId: string): Promise<void> {
  await request<unknown>(`${PREFIX}/documents/${docId}`, { method: 'DELETE' })
}

export async function reindexDocument(docId: string): Promise<DocumentItem> {
  const data = await request<SnakeDoc>(`${PREFIX}/documents/${docId}/reindex`, { method: 'POST' })
  return mapDoc(data)
}

async function ensureConversation(kbId: string): Promise<string> {
  const existing = conversationByKb.get(kbId)
  if (existing) return existing
  const data = await request<SnakeConversation>(`${PREFIX}/conversations`, {
    method: 'POST',
    body: { kb_id: kbId },
  })
  conversationByKb.set(kbId, data.id)
  return data.id
}

export async function chat(req: ChatRequest): Promise<ChatResponse> {
  if (!req.kbId) throw new ApiError(400, '请先选择知识库')
  const q = req.question.trim()
  if (!q) throw new ApiError(400, '请输入问题')

  const convId = await ensureConversation(req.kbId)
  let data: SnakeChatData
  try {
    data = await request<SnakeChatData>(`${PREFIX}/conversations/${convId}/messages`, {
      method: 'POST',
      body: { content: q },
    })
  } catch (e) {
    // Stale conversation id — recreate once
    if (e instanceof ApiError && (e.status === 404 || e.code === 40401)) {
      conversationByKb.delete(req.kbId)
      const fresh = await ensureConversation(req.kbId)
      data = await request<SnakeChatData>(`${PREFIX}/conversations/${fresh}/messages`, {
        method: 'POST',
        body: { content: q },
      })
    } else {
      throw e
    }
  }

  const answer = data.assistant_message?.content ?? ''
  const citations = (data.assistant_message?.citations || []).map(mapCitation)
  const noHitText = '知识库中未找到相关内容'
  const hit = citations.length > 0 && answer !== noHitText

  return { answer, citations, hit }
}

export async function listMembers(): Promise<Member[]> {
  const data = await request<PageResult<SnakeMember> | SnakeMember[]>(`${PREFIX}/members`)
  const items = Array.isArray(data) ? data : data.items || []
  return items.map(mapMember)
}

export async function inviteMember(_body: InviteMemberRequest): Promise<Member> {
  throw new ApiError(501, '当前后端未开放邀请接口（契约：首期不做公开注册/邀请）')
}

export { ApiError }
