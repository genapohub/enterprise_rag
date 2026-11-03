# 企业 RAG 知识库 · 前端（Vue3）

> 对齐：`02-产品文档/企业RAG_一页纸定位_v0.1.md`、`03-技术文档/企业RAG_API契约_v0.1.md`、`05-UIUX设计/`  
> 本轮：**默认接真后端** `http://127.0.0.1:8088`（`/api/v1`）；`VITE_USE_MOCK=true` 可回退本地 Mock。

## 栈

- Vite + Vue 3 + TypeScript + Vue Router + Pinia
- 样式：`src/styles/tokens.css` + `pages.css`
- 强调色：青绿 `#0e7490`（`--color-accent`）；石墨侧栏

## 手启步骤

### 1) 后端（请人手启，AI 不代启常驻）

```bash
cd /Users/macos/Downloads/WorkBuddy/企业RAG知识库/06-项目编码/enterprise_rag_api
# 依赖与 DB 按该目录 README；常见：
# source .venv/bin/activate && uvicorn app.main:app --reload --port 8088
# 或 PyCharm 运行配置「API FastAPI 8088」
```

探活：`curl http://127.0.0.1:8088/healthz`

种子账号见后端 **`.env.example`**：`BOOTSTRAP_ADMIN_USER=admin` / `BOOTSTRAP_ADMIN_PASSWORD=changeme`（勿把该口令当生产密钥叙事）。

### 2) 前端

```bash
cd /Users/macos/Downloads/WorkBuddy/企业RAG知识库/06-项目编码/enterprise-rag-web
cp -n .env.example .env   # 可选
npm install
npm run dev               # http://localhost:3080 ；proxy → VITE_API_TARGET
```

构建校验：

```bash
npm run build
```

### Mock 开关

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `VITE_API_TARGET` | `http://127.0.0.1:8088` | Vite `server.proxy` 目标（`/api`、`/healthz`） |
| `VITE_USE_MOCK` | `false` | `true` 时走 `src/mock/`，不打后端 |

Mock 种子（仅 Mock）：`admin` / `admin123` · `chenke` / `member123`

## 真 API 端点（前端已接）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | → access_token + user（snake→camel） |
| GET | `/api/v1/auth/me` | 当前用户 |
| GET/POST | `/api/v1/knowledge-bases` | 分页 `items` / 创建 |
| GET | `/api/v1/knowledge-bases/{id}` | 详情 |
| GET/POST | `/api/v1/knowledge-bases/{id}/documents` | 列表 / multipart `file` |
| DELETE | `/api/v1/documents/{id}` | 软删 |
| POST | `/api/v1/documents/{id}/reindex` | 失败态重试 |
| POST | `/api/v1/conversations` + `.../{id}/messages` | 问答；用 answer/citations |
| GET | `/api/v1/members` | admin |

统一响应：`{ code, data, message }`；`code!==0` 抛错。文档状态：`uploaded/parsing/chunking/indexing/ready/parse_failed/index_failed`。

## 路由表

| 路径 | 页面 |
| --- | --- |
| `/login` | 登录 |
| `/knowledge-bases` | 知识库列表 |
| `/knowledge-bases/:id/docs` | 文档管理 |
| `/chat` | 对话 |
| `/members` | 成员（admin） |

## 目录要点

```
src/
  api/          http.ts + client.ts + index（Mock 开关）
  mock/         本地 Mock（VITE_USE_MOCK=true）
  components/   AppSidebar, EmptyState, StatusBadge
  layouts/      AppLayout
  views/        Login / KnowledgeBases / Documents / Chat / Members
  stores/       auth
  styles/       tokens.css + pages.css
  types/api.ts
```

## 硬门禁

- 禁 emoji 功能图标（SVG）
- 禁硬编码色（除 `#fff`/`#000`）；用 `var(--token)`
- 禁紫粉渐变、`#6366f1`、Welcome/Lorem
- **禁止修改** `05-UIUX设计/` 真源目录

## 端口

- web dev/preview：**3080**
- api：**8088**（经 Vite proxy）
