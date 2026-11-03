# 企业 RAG 知识库 · API 契约 v0.1

> 对齐：`企业RAG_一页纸定位_v0.1.md` · `企业RAG_技术选型_v0.1.md`  
> 落盘：2026-11-02 Asia/Shanghai · 单组织 Web RAG MVP  
> 不做：多租户、机器人、SSO、OCR  
> OpenAPI：同目录 `企业RAG_openapi_v0.1.yaml`

## 0. 约定

| 项 | 约定 |
| --- | --- |
| Base | `http://localhost:8088` |
| 前缀 | `/api/v1`（`/healthz` 除外） |
| 鉴权 | `Authorization: Bearer <access_token>` |
| 统一响应 | `{ "code": 0, "data": {}, "message": "" }` |
| 成功 code | `0` |
| 内容类型 | `application/json`；上传用 `multipart/form-data` |
| 时间 | ISO-8601 UTC（`...Z`）；客户端按需转本地 |
| 角色 | `admin` \| `member` |

### 错误码（业务 `code`，HTTP 仍分层）

| code | HTTP | 含义 |
| --- | --- | --- |
| 0 | 2xx | 成功 |
| 40001 | 400 | 参数校验失败 |
| 40101 | 401 | 未登录 / token 无效或过期 |
| 40301 | 403 | 无权限 |
| 40401 | 404 | 资源不存在 |
| 40901 | 409 | 业务冲突（如重名、状态不允许） |
| 42901 | 429 | 限流 |
| 50001 | 500 | 服务器内部错误（不吐堆栈） |

---

## 1. 文档状态机

```
uploaded → parsing → chunking → indexing → ready
                ↘ parse_failed
                           ↘（chunking/indexing 失败）→ index_failed
```

| 状态 | 含义 | 可读失败字段 |
| --- | --- | --- |
| `uploaded` | 文件已落盘，待解析 | — |
| `parsing` | 正在解析 | — |
| `parse_failed` | 解析失败 | `fail_reason` 必填 |
| `chunking` | 切块中 | — |
| `indexing` | 写向量/索引中 | — |
| `ready` | 可检索问答 | — |
| `index_failed` | 切块或索引失败 | `fail_reason` 必填 |

附加生命周期字段（非状态机节点）：

| 字段 | 说明 |
| --- | --- |
| `is_archived` | 下架：检索不再命中；历史引用快照可保留 |
| `deleted_at` | 软删时间；列表默认不返回已删 |

合法迁移（服务端强制）：

- `uploaded` → `parsing`
- `parsing` → `chunking` \| `parse_failed`
- `chunking` → `indexing` \| `index_failed`
- `indexing` → `ready` \| `index_failed`
- `parse_failed` / `index_failed` → `parsing`（管理员触发重试）

---

## 2. 引用结构（问答必带）

答案 `data.answer` 可为空串（无命中时）；`citations` **始终为数组**（可空）。

有检索命中并作答时，至少 1 条 citation：

```json
{
  "doc_id": "uuid",
  "doc_name": "员工手册.pdf",
  "chunk_id": "uuid",
  "snippet": "……原文片段……",
  "page": 3,
  "score": 0.82
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `doc_id` | string(uuid) | ✓ | 文档 ID |
| `doc_name` | string | ✓ | 展示名 |
| `chunk_id` | string(uuid) | ✓ | 块 ID |
| `snippet` | string | ✓ | 引用预览（可截断） |
| `page` | int \| null | | PDF 页码等 |
| `score` | float \| null | | 检索分 |

无命中口径：`answer` = 「知识库中未找到相关内容」；`citations` = `[]`。

---

## 3. 核心资源与端点

### 3.1 Health

| Method | Path | Auth | 说明 |
| --- | --- | --- | --- |
| GET | `/healthz` | 无 | `{ status, db, version }`；`status=ok` 即绿 |

### 3.2 Auth

| Method | Path | Auth | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | 无 | — | body: `{username,password}` → tokens + user |
| POST | `/api/v1/auth/refresh` | 无 | — | body: `{refresh_token}` → 新 access（可含 refresh） |
| GET | `/api/v1/auth/me` | Bearer | 任一 | 当前用户 |

**Login 响应 data：**

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "id": "uuid", "username": "admin", "display_name": "管理员", "role": "admin" }
}
```

限流：login ≤10 次/分/IP（文档口径；骨架可内存计数）。

### 3.3 Knowledge Bases

| Method | Path | Auth | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/knowledge-bases` | Bearer | 任一 | 列表（未归档默认） |
| POST | `/api/v1/knowledge-bases` | Bearer | admin | 创建 |
| GET | `/api/v1/knowledge-bases/{kb_id}` | Bearer | 任一 | 详情 |
| PATCH | `/api/v1/knowledge-bases/{kb_id}` | Bearer | admin | 改名/描述 |
| POST | `/api/v1/knowledge-bases/{kb_id}/archive` | Bearer | admin | 归档 |
| POST | `/api/v1/knowledge-bases/{kb_id}/unarchive` | Bearer | admin | 取消归档 |

**KB 对象：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | |
| `name` | string | 1–128 |
| `description` | string | 可空 |
| `is_archived` | bool | |
| `doc_count` | int | 未删文档数 |
| `created_at` / `updated_at` | datetime | |

创建 body：`{ "name": "...", "description": "" }`

### 3.4 Documents

| Method | Path | Auth | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/knowledge-bases/{kb_id}/documents` | Bearer | 任一 | 列表 |
| POST | `/api/v1/knowledge-bases/{kb_id}/documents` | Bearer | admin | multipart 上传 `file` |
| GET | `/api/v1/documents/{doc_id}` | Bearer | 任一 | 详情（含状态机字段） |
| POST | `/api/v1/documents/{doc_id}/archive` | Bearer | admin | 下架 |
| POST | `/api/v1/documents/{doc_id}/unarchive` | Bearer | admin | 重新上架（不自动重索引） |
| DELETE | `/api/v1/documents/{doc_id}` | Bearer | admin | 软删 + 向量点清理 |
| POST | `/api/v1/documents/{doc_id}/reindex` | Bearer | admin | 失败态重试 → `parsing` |

**Document 对象（状态机字段齐）：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | uuid | |
| `kb_id` | uuid | |
| `name` | string | 原始文件名 |
| `content_type` | string | |
| `size_bytes` | int | |
| `status` | enum | 见 §1 |
| `fail_reason` | string \| null | 失败必填可读原因 |
| `is_archived` | bool | |
| `chunk_count` | int | ready 后 >0 |
| `created_at` / `updated_at` | datetime | |
| `indexed_at` | datetime \| null | 进入 ready 时间 |

允许扩展名：`.pdf` `.docx` `.md` `.txt`；单文件上限默认 20MB（可配）。

### 3.5 Conversations & Messages（问答）

| Method | Path | Auth | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/conversations` | Bearer | 任一 | 当前用户会话列表；可 `?kb_id=` |
| POST | `/api/v1/conversations` | Bearer | 任一 | `{kb_id, title?}` |
| GET | `/api/v1/conversations/{id}` | Bearer | 本人 | 详情 |
| GET | `/api/v1/conversations/{id}/messages` | Bearer | 本人 | 消息列表 |
| POST | `/api/v1/conversations/{id}/messages` | Bearer | 任一(库内) | 非流式问答 |
| POST | `/api/v1/conversations/{id}/messages:stream` | Bearer | 任一 | **SSE stub**（MVP 可 501/占位） |
| DELETE | `/api/v1/conversations/{id}` | Bearer | 本人 | 删会话 |

**提问 body：** `{ "content": "请假要提前几天？" }`

**问答响应 data：**

```json
{
  "user_message": { "id": "uuid", "role": "user", "content": "...", "created_at": "..." },
  "assistant_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "...",
    "citations": [
      {
        "doc_id": "uuid",
        "doc_name": "手册.pdf",
        "chunk_id": "uuid",
        "snippet": "...",
        "page": null,
        "score": 0.91
      }
    ],
    "created_at": "..."
  }
}
```

### 3.6 Members

| Method | Path | Auth | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/members` | Bearer | admin | 简单成员列表 |
| PATCH | `/api/v1/members/{user_id}` | Bearer | admin | 改 `role` 或 `is_active`（可选 MVP） |

**Member：** `{ id, username, display_name, role, is_active, created_at }`

首期不做邀请/注册公开接口；种子管理员由 `BOOTSTRAP_ADMIN_*` 创建。骨架可另提供仅测试用 seed。

---

## 4. 权限矩阵（摘要）

| 动作 | admin | member |
| --- | --- | --- |
| 登录 / me / 自己的会话问答 | ✓ | ✓ |
| KB CRUD / 归档 | ✓ | 列表+详情只读 |
| 文档上传/下架/删除/重索引 | ✓ | 列表+详情只读 |
| 成员列表 | ✓ | ✗ |
| 已归档 KB 上新建会话 | ✗（409） | ✗ |

---

## 5. 分页（列表通用）

Query：`page`（默认 1）· `page_size`（默认 20，最大 100）  
data：`{ "items": [], "total": 0, "page": 1, "page_size": 20 }`

---

## 6. 与选型对齐的环境键（仅 example）

见编码目录 `.env.example`：`POSTGRES_*` · `QDRANT_URL` · `EMBEDDING_*` · `LLM_*` · `JWT_SECRET` · `BOOTSTRAP_ADMIN_*` · `API_PORT=8088` · `WEB_PORT=3080`。  
无 key 时 Embedding/LLM **走 stub**，状态机仍可推到 `ready`（README 写明）。

---

## 落盘

- 契约：`03-技术文档/企业RAG_API契约_v0.1.md`
- OpenAPI：`03-技术文档/企业RAG_openapi_v0.1.yaml`
