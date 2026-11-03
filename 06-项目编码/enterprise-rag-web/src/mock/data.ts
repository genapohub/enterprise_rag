import type { DocumentItem, KnowledgeBase, Member, User } from '@/types/api'

export const SEED_USERS: Array<User & { password: string }> = [
  {
    id: 'u-admin',
    username: 'admin',
    password: 'admin123',
    displayName: '张明',
    role: 'admin',
  },
  {
    id: 'u-member',
    username: 'chenke',
    password: 'member123',
    displayName: '陈可',
    role: 'member',
  },
]

export let knowledgeBases: KnowledgeBase[] = [
  {
    id: 'kb-hr',
    name: '人事制度库',
    description: '员工手册、请假与考勤、薪酬福利相关制度文档。',
    docCount: 3,
    updatedAt: '2026-11-01T10:20:00+08:00',
  },
  {
    id: 'kb-it',
    name: 'IT 运维手册',
    description: '账号申请、VPN、故障排查与变更流程。',
    docCount: 2,
    updatedAt: '2026-10-28T16:05:00+08:00',
  },
  {
    id: 'kb-fin',
    name: '财务报销指引',
    description: '差旅、招待、采购报销口径与模板。',
    docCount: 0,
    updatedAt: '2026-10-15T09:00:00+08:00',
  },
]

export let documents: DocumentItem[] = [
  {
    id: 'doc-1',
    kbId: 'kb-hr',
    name: '员工手册_v2026.pdf',
    format: 'pdf',
    sizeLabel: '1.2 MB',
    status: 'ready',
    updatedAt: '2026-11-01T09:10:00+08:00',
  },
  {
    id: 'doc-2',
    kbId: 'kb-hr',
    name: '请假与考勤制度.docx',
    format: 'docx',
    sizeLabel: '240 KB',
    status: 'indexing',
    updatedAt: '2026-11-02T14:30:00+08:00',
  },
  {
    id: 'doc-3',
    kbId: 'kb-hr',
    name: '薪酬福利说明.md',
    format: 'md',
    sizeLabel: '36 KB',
    status: 'ready',
    updatedAt: '2026-10-30T11:00:00+08:00',
  },
  {
    id: 'doc-4',
    kbId: 'kb-it',
    name: 'VPN接入指南.pdf',
    format: 'pdf',
    sizeLabel: '860 KB',
    status: 'ready',
    updatedAt: '2026-10-28T15:40:00+08:00',
  },
  {
    id: 'doc-5',
    kbId: 'kb-it',
    name: '坏扫描件.pdf',
    format: 'pdf',
    sizeLabel: '4.1 MB',
    status: 'parse_failed',
    statusReason: '无法抽取文本（疑似扫描件，本期不做 OCR）',
    updatedAt: '2026-10-27T18:12:00+08:00',
  },
]

export let members: Member[] = [
  {
    id: 'u-admin',
    username: 'admin',
    displayName: '张明',
    role: 'admin',
    status: 'active',
    joinedAt: '2026-09-01',
  },
  {
    id: 'u-member',
    username: 'chenke',
    displayName: '陈可',
    role: 'member',
    status: 'active',
    joinedAt: '2026-09-12',
  },
  {
    id: 'u-3',
    username: 'liwei',
    displayName: '李伟',
    role: 'member',
    status: 'active',
    joinedAt: '2026-10-08',
  },
]
