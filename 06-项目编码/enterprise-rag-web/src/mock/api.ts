import type {
  ChatRequest,
  ChatResponse,
  DocumentItem,
  InviteMemberRequest,
  KnowledgeBase,
  LoginRequest,
  LoginResponse,
  Member,
} from '@/types/api'
import * as db from './data'

const delay = (ms = 420) => new Promise((r) => setTimeout(r, ms))

function uid(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 9)}`
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** Mock: POST /api/auth/login */
export async function login(body: LoginRequest): Promise<LoginResponse> {
  await delay(550)
  const found = db.SEED_USERS.find(
    (u) => u.username === body.username.trim() && u.password === body.password,
  )
  if (!found) {
    throw new ApiError(401, '账号或密码不正确')
  }
  const { password: _pw, ...user } = found
  void _pw
  return {
    accessToken: `mock-jwt.${user.id}.${Date.now()}`,
    user,
  }
}

/** Mock: GET /api/knowledge-bases */
export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  await delay()
  return db.knowledgeBases.filter((k) => !k.archived).map((k) => ({ ...k }))
}

/** Mock: POST /api/knowledge-bases */
export async function createKnowledgeBase(input: {
  name: string
  description?: string
}): Promise<KnowledgeBase> {
  await delay(500)
  const kb: KnowledgeBase = {
    id: uid('kb'),
    name: input.name.trim(),
    description: (input.description || '').trim() || '暂无描述',
    docCount: 0,
    updatedAt: new Date().toISOString(),
  }
  db.knowledgeBases.unshift(kb)
  return { ...kb }
}

/** Mock: GET /api/knowledge-bases/:id */
export async function getKnowledgeBase(id: string): Promise<KnowledgeBase> {
  await delay(280)
  const kb = db.knowledgeBases.find((k) => k.id === id)
  if (!kb) throw new ApiError(404, '知识库不存在')
  return { ...kb }
}

/** Mock: GET /api/knowledge-bases/:id/documents */
export async function listDocuments(kbId: string): Promise<DocumentItem[]> {
  await delay(480)
  if (kbId === 'kb-error') {
    throw new ApiError(500, '加载文档列表失败，请稍后重试')
  }
  return db.documents.filter((d) => d.kbId === kbId).map((d) => ({ ...d }))
}

/** Mock: POST /api/knowledge-bases/:id/documents */
export async function uploadDocument(
  kbId: string,
  file: File | { name: string; size: number },
): Promise<DocumentItem> {
  await delay(700)
  if (file.name.toLowerCase().includes('fail')) {
    throw new ApiError(400, '上传失败：文件校验未通过（Mock：文件名含 fail）')
  }
  const ext = file.name.split('.').pop()?.toLowerCase() || 'txt'
  const size = 'size' in file ? file.size : 0
  const doc: DocumentItem = {
    id: uid('doc'),
    kbId,
    name: file.name,
    format: ext,
    sizeLabel:
      size > 1024 * 1024
        ? `${(size / (1024 * 1024)).toFixed(1)} MB`
        : `${Math.max(1, Math.round(size / 1024))} KB`,
    status: 'uploaded',
    updatedAt: new Date().toISOString(),
  }
  db.documents.unshift(doc)
  const kb = db.knowledgeBases.find((k) => k.id === kbId)
  if (kb) {
    kb.docCount += 1
    kb.updatedAt = doc.updatedAt
  }
  window.setTimeout(() => {
    const d = db.documents.find((x) => x.id === doc.id)
    if (d && d.status === 'uploaded') d.status = 'parsing'
  }, 600)
  window.setTimeout(() => {
    const d = db.documents.find((x) => x.id === doc.id)
    if (d && d.status === 'parsing') d.status = 'chunking'
  }, 1200)
  window.setTimeout(() => {
    const d = db.documents.find((x) => x.id === doc.id)
    if (d && d.status === 'chunking') d.status = 'indexing'
  }, 1800)
  window.setTimeout(() => {
    const d = db.documents.find((x) => x.id === doc.id)
    if (d && d.status === 'indexing') d.status = 'ready'
  }, 3200)
  return { ...doc }
}

/** Mock: DELETE /api/knowledge-bases/:id/documents/:docId */
export async function deleteDocument(kbId: string, docId: string): Promise<void> {
  await delay(400)
  const idx = db.documents.findIndex((d) => d.id === docId && d.kbId === kbId)
  if (idx < 0) throw new ApiError(404, '文档不存在')
  db.documents.splice(idx, 1)
  const kb = db.knowledgeBases.find((k) => k.id === kbId)
  if (kb) {
    kb.docCount = Math.max(0, kb.docCount - 1)
    kb.updatedAt = new Date().toISOString()
  }
}

/** Mock: POST /api/chat */
export async function chat(req: ChatRequest): Promise<ChatResponse> {
  await delay(900)
  const q = req.question.trim()
  if (!req.kbId) throw new ApiError(400, '请先选择知识库')
  if (!q) throw new ApiError(400, '请输入问题')

  if (q.includes('触发错误') || q.toLowerCase().includes('force-error')) {
    throw new ApiError(502, '对话服务暂时不可用')
  }

  const noHit =
    /火星|外太空|股价预测|无关|随便问问/.test(q) || q.includes('知识库外')

  const kbDocs = db.documents.filter((d) => d.kbId === req.kbId && d.status === 'ready')
  const primary = kbDocs[0]
  const secondary = kbDocs[1]

  if (noHit || !primary) {
    return {
      hit: false,
      answer: '知识库中未找到相关内容',
      citations: [],
    }
  }

  const topic = q.replace(/[？?。.!！]/g, '')
  return {
    hit: true,
    answer:
      `根据「${primary.name}」等文档：与「${topic}」相关的规定已收录。` +
      '请以引用片段为准；若条款有更新，以管理员最新上传版本为准。',
    citations: [
      {
        docId: primary.id,
        docName: primary.name,
        snippet: '……员工应遵守组织制度；具体流程以现行手册章节为准，疑问可向人事咨询……',
        page: 3,
        score: 0.86,
      },
      ...(secondary
        ? [
            {
              docId: secondary.id,
              docName: secondary.name,
              snippet: '……相关申请需经直属主管确认后提交系统；紧急情况可事后补办……',
              page: 1,
              score: 0.72,
            },
          ]
        : []),
    ],
  }
}

/** Mock: GET /api/members */
export async function listMembers(): Promise<Member[]> {
  await delay()
  return db.members.map((m) => ({ ...m }))
}

/** Mock: POST /api/members */
export async function inviteMember(body: InviteMemberRequest): Promise<Member> {
  await delay(500)
  if (db.members.some((m) => m.username === body.username.trim())) {
    throw new ApiError(409, '该账号已存在')
  }
  const m: Member = {
    id: uid('u'),
    username: body.username.trim(),
    displayName: body.displayName.trim() || body.username.trim(),
    role: body.role,
    status: 'active',
    joinedAt: new Date().toISOString().slice(0, 10),
  }
  db.members.unshift(m)
  return { ...m }
}
