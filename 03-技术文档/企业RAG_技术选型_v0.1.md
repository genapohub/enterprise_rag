# 企业 RAG 知识库 · 技术选型 v0.1

> 对齐：`02-产品文档/企业RAG_一页纸定位_v0.1.md` · 设计已过线（`05-UIUX设计/`）  
> 场景：单组织 Web 问答 MVP · 栈默认 FastAPI + Vue3 + Docker Compose  
> 落盘：2026-11-02 Asia/Shanghai · **非部署证明**；本文仅选型默认，未起服务  
> 不做：多租户、机器人、SSO、OCR/音视频、Agent 编排

## 0. 推荐默认栈（一句话）

**FastAPI + Vue3 + Postgres + Qdrant +（解析 PyMuPDF/python-docx）+ Embedding 走硅基流动 BGE-M3 API + LLM 走 OpenAI 兼容网关（默认 DeepSeek）+ 本地 JWT；Compose 一键起。**

---

## 1. 文档解析（PDF / docx / md / txt）

| 方案 | 格式覆盖 | 优点 | 缺点 | MVP 适配 |
| --- | --- | --- | --- | --- |
| **A. PyMuPDF + python-docx + 原生 md/txt（推荐）** | PDF/docx/md/txt | 纯 Python、安装轻、中文 PDF 抽字稳、Compose 无额外服务 | 复杂排版/扫描件弱（OCR 本期不做） | ✅ |
| B. unstructured | 广 | 版面策略多 | 依赖重、冷启动慢、镜像肥 | 二期再议 |
| C. pypdf + python-docx | PDF/docx | 更轻 | 部分 PDF 抽字质量不如 PyMuPDF | 备选降级 |

**推荐默认：A。**  
- PDF → `pymupdf`（`fitz`）按页抽纯文本  
- Word → `python-docx` 段落拼接  
- Markdown / 纯文本 → 直接读 UTF-8（坏编码尝试 `gb18030` 回退一次）  
- 解析失败：落文档状态 `parse_failed` + 可读原因（对齐产品验收）

---

## 2. 切块策略（默认参数）

| 方案 | 思路 | 默认参数 | 备注 |
| --- | --- | --- | --- |
| **A. 递归字符切块（推荐）** | 段 → 句 → 字符 | 见下 | 中文友好、实现简单 |
| B. 按 token（tiktoken） | 精确控上下文 | chunk=512 / overlap=64 | 需绑定具体 tokenizer；API 嵌入时可选 |
| C. 按页/按标题 | 结构保留强 | — | md 可辅以标题边界；PDF 页界作硬上限 |

**推荐默认：A（递归字符），参数写死进配置可改：**

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `chunk_size` | **800**（字符） | 约合中文 400～500 token 量级，适配常见 8k 上下文检索拼装 |
| `chunk_overlap` | **120**（字符） | ≈15%，减少句中切断丢义 |
| `separators` | `\n\n` → `\n` → `。！？；` → ` ` → `""` | 优先段落后句子 |
| 硬上限 | 单块 ≤ 1200 字符 | 异常超长段强制再切 |
| 元数据随块 | `kb_id, doc_id, chunk_index, source_page?, heading?` | 引用回链用 |

md 额外：若识别到 ATFx` 标题，优先在标题边界切开（仍受 `chunk_size` 约束）。

---

## 3. Embedding 模型（国内可用优先）

| 方案 | 形态 | 费用/依赖 | 国内可达 | MVP |
| --- | --- | --- | --- | --- |
| **A. 硅基流动 SiliconFlow · `BAAI/bge-m3`（推荐）** | HTTPS API | 按量；只需 `SILICONFLOW_API_KEY`；无本机 GPU | ✅ | ✅ |
| B. 本机 `bge-large-zh-v1.5` / `bge-m3`（sentence-transformers / onnx） | 容器内推理 | 免费调用但镜像大、CPU 慢、需模型权重挂载 | ✅（无外网也可） | 内网/离线备选 |
| C. 阿里云百炼 / DashScope text-embedding-v3 | API | 按量；阿里云账号 | ✅ | 备选 |
| D. OpenAI `text-embedding-3-small` | API | 需国际网络与账单 | ⚠️ 常不稳定 | 不作为默认 |

**推荐默认：A（硅基流动 BGE-M3 API）。**  
- 向量维：**1024**（bge-m3；入库与检索配置必须一致）  
- 批处理：上传索引时 `batch_size=32`  
- 配置项：`EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` / `EMBEDDING_MODEL`（可改本机或其它兼容端点，不改代码）  
- **备选切换条件**：无外网或强制数据不出域 → 切 B（Compose profile `local-embed`），接受首次拉模型与更慢索引

---

## 4. 向量库（Compose 可起）

| 方案 | Compose | 过滤/多库 | 运维 | 推荐 |
| --- | --- | --- | --- | --- |
| **A. Qdrant（推荐）** | 官方镜像一行 | payload 按 `kb_id`/`doc_id` 过滤成熟 | 独立服务；REST+gRPC | ✅ 默认 |
| **B. pgvector（备选）** | 随 Postgres 镜像 | SQL 过滤简单 | **少一个容器**；大库性能与专用库有差距 | ✅ 备选 |
| C. Milvus standalone | 可起但组件多 | 强 | 偏重 | 不做首期 |
| D. Chroma | 可 | 简单 | 生产语义弱、备份习惯差 | 不选 |

**推荐默认：A Qdrant；备选 B pgvector（若强烈希望只养一个有状态服务）。**  
- Collection 建议：按知识库 `kb_{id}` 或单 collection + 强制 `kb_id` filter（**默认单 collection + filter**，少集合管理）  
- 下架/删文档：按 `doc_id` 删点，保证后续检索不再命中（对齐验收）

---

## 5. LLM 对话（可配置 API Key · 网关形态）

| 方案 | 形态 | 国内 | 说明 |
| --- | --- | --- | --- |
| **A. OpenAI 兼容 SDK + 可配 `BASE_URL`（推荐）** | 应用内直接调；env 注入 | 取决于上游 | **一种代码多上游** |
| B. 自建 LiteLLM / 一店网关容器 | 多模型路由 | 可 | MVP 多一容器，暂不默认 |
| C. 只绑单一厂商 SDK | 厂商包 | — | 锁死，不选 |

**推荐默认上游：DeepSeek Chat（OpenAI 兼容）。**  

| 项 | 默认 |
| --- | --- |
| 协议 | OpenAI Chat Completions（支持流式 SSE） |
| `LLM_BASE_URL` | `https://api.deepseek.com` |
| `LLM_MODEL` | `deepseek-chat` |
| `LLM_API_KEY` | 环境变量，**禁止写进镜像** |
| 备选上游 | 硅基流动上的 Qwen/DeepSeek；或通义 DashScope 兼容模式（改 BASE_URL/MODEL/KEY 即可） |

行为约束（产品口径进系统提示）：  
- 仅依据检索片段作答；无命中回复固定口径「知识库中未找到相关内容」  
- 每条成功作答至少带回 1 条引用（文档名 + 片段）；前端可点

---

## 6. 元数据 / 引用怎么存（业务库 + 向量库分工）

| 存储 | 引擎（推荐） | 存什么 |
| --- | --- | --- |
| **业务库** | **PostgreSQL 16** | 用户、角色、知识库、文档元数据与解析/索引状态、会话与消息、**引用关联表**、审计轻量字段 |
| **向量库** | **Qdrant** | `embedding` + payload（`kb_id, doc_id, chunk_id, chunk_index, text`） |
| 备选合一 | Postgres + pgvector | 向量也放 PG；引用与业务同库事务更简单 |

**引用链路（默认）：**

1. 索引：解析 → 切块 → 写 `chunks` 表（Postgres，含原文片段）→ 向量写入 Qdrant（payload 带 `chunk_id`）  
2. 检索：Qdrant top-k → 用 `chunk_id` 回表补全文档名/页码  
3. 作答落库：`messages` + `message_citations(message_id, chunk_id, score, snip_preview)`  
4. 删文档：事务内标文档删除/下架 → 删 Qdrant 点 → 会话历史引用可保留快照文案，但新问答不再命中  

**不选 MySQL 的原因（本 MVP）：** pgvector 备选路径一致、JSON/数组更好用；若组织强制 MySQL，业务库可换 MySQL 8，向量仍用 Qdrant（推荐组合不变）。

---

## 7. 鉴权（本地即可）

| 方案 | 说明 | MVP |
| --- | --- | --- |
| **A. JWT（access + refresh）+ bcrypt 密码（推荐）** | Vue3 带 `Authorization: Bearer`；refresh 存 httpOnly cookie 或本地二选一，**默认 refresh 也走 body/local 简化** | ✅ |
| B. 服务端 session + cookie | 实现简单但多实例要粘滞/共享存储 | 备选 |
| C. SSO / OIDC | 产品明确二期 | ❌ 首期不做 |

角色：`admin` | `member`（对齐设计说明权限表）。  
种子：Compose 首次启动可建管理员（env：`BOOTSTRAP_ADMIN_USER/PASSWORD`）。

---

## 8. Compose 服务清单与端口

> 避开常见占用：**不用 8010、不用 5173**。开发与预览端口如下（可在 `.env` 覆盖）。

| 服务 | 镜像/构建 | 宿主端口 | 容器内 | 职责 |
| --- | --- | --- | --- | --- |
| `web` | 构建 Vue3 → nginx 静态 | **3080** | 80 | 前端；反代 `/api` → api |
| `api` | FastAPI（uvicorn） | **8088** | 8000 | REST + SSE 对话 |
| `db` | postgres:16-alpine | **5432** | 5432 | 业务元数据 |
| `qdrant` | qdrant/qdrant:v1.12+ | **6333**（HTTP）/ **6334**（gRPC） | 同左 | 向量检索 |
| （可选 profile）`embed` | 本机嵌入推理 | 无对外或 8090 | — | 仅离线 embedding 时启用 |

**建议 `.env` 键（无密钥入库）：**

```bash
POSTGRES_USER=rag
POSTGRES_PASSWORD=changeme
POSTGRES_DB=enterprise_rag
QDRANT_URL=http://qdrant:6333
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=BAAI/bge-m3
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=
LLM_MODEL=deepseek-chat
JWT_SECRET=changeme-in-prod
BOOTSTRAP_ADMIN_USER=admin
BOOTSTRAP_ADMIN_PASSWORD=changeme
WEB_PORT=3080
API_PORT=8088
```

健康检查：`GET http://localhost:8088/healthz`（产品验收口径）。

本地前端热更新（可选，非 Compose 必需）：Vite **5174**（显式避开 5173）。

---

## 9. 默认参数速查表

| 域 | 默认 |
| --- | --- |
| 解析 | PyMuPDF + python-docx + 原生 md/txt |
| 切块 | 800 / overlap 120；递归分隔符 |
| Embedding | 硅基流动 `BAAI/bge-m3`（1024 维） |
| 向量库 | Qdrant（备选 pgvector） |
| LLM | OpenAI 兼容 · DeepSeek `deepseek-chat` |
| 业务库 | PostgreSQL 16 |
| 鉴权 | JWT + bcrypt；admin/member |
| 端口 | web 3080 · api 8088 · pg 5432 · qdrant 6333/6334 |

---

## 10. 待拍板分歧（最多 2 个 · 均已给默认）

1. **向量库：Qdrant（默认） vs pgvector（少容器）**  
   - 默认 **Qdrant**。若哥拿坡要求「有状态只留 Postgres」→ 改 pgvector，API 检索仓储换适配器即可。

2. **Embedding：云 API 硅基流动（默认） vs 本机 bge**  
   - 默认 **硅基流动 API**（省 GPU/镜像）。若文档敏感、禁止出域 → Compose profile 启本机模型，成本是首次下载与索引变慢。

（LLM 上游 DeepSeek / 通义 / 硅基流动上的模型均为同一 OpenAI 兼容形态，**不单独列为分歧**，用 env 切换。）

---

## 11. 下一步（非本文范围）

1. 哥拿坡确认 §10 两项（或不反对则按默认）  
2. 写 API 契约（OpenAPI）与库表草图 → `06-项目编码/` 建仓  
3. 后/前并行；禁止在选型未确认前擅自拉起常驻进程（见根目录 `AGENTS.md`）

## 落盘路径

`/Users/macos/Downloads/WorkBuddy/企业RAG知识库/03-技术文档/企业RAG_技术选型_v0.1.md`
