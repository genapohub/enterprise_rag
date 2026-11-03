# 企业 RAG 知识库

> **单组织 Web 问答 MVP** · 设计先行 · 2026-11-02 立项 · 默认分支 `main`
>
> 仓库状态：**代码骨架 + 高保真静态设计稿，未部署、未拉起常驻服务**。这是可跑通链路的 MVP，不是生产可用系统。上线前请先看「已知限制」。

## 一句话

企业内部员工上传文档，用自然语言提问，**答案必须带可点击的来源引用**；管理员管知识库与成员。检索无命中时明确回复「知识库中未找到相关内容」，不允许把编造内容当事实。

---

## 当前进度（截至 2026-11-03）

| 阶段 | 状态 | 产物 |
| --- | --- | --- |
| 产品定位与验收口径 | 完成 | `02-产品文档/企业RAG_一页纸定位_v0.1.md` |
| 关键页设计稿 | 完成 | `05-UIUX设计/`（5 页静态 HTML + `tokens.css`，浏览器直接打开可审） |
| 技术选型 | 完成 | `03-技术文档/企业RAG_技术选型_v0.1.md` |
| API 契约 + OpenAPI | 完成 | `03-技术文档/企业RAG_API契约_v0.1.md`、`企业RAG_openapi_v0.1.yaml`（18 个路径） |
| 后端 FastAPI | 骨架完成 | `06-项目编码/enterprise_rag_api/`（分层路由、文档状态机、引用、JWT、stub 降级、冒烟测试） |
| 前端 Vue3 | 完成 | `06-项目编码/enterprise-rag-web/`（5 页，默认接真 `/api/v1`，`VITE_USE_MOCK=true` 可回退 Mock） |
| 部署 / 常驻服务 | **未做** | 需手启；AI 不代启（见 `AGENTS.md`） |

---

## 首期做 / 不做

**做（MVP 六条）**

1. 本地账号登录（不做 SSO）
2. 知识库列表 / 新建 / 归档
3. 文档上传：PDF、`.docx`、`.md`、`.txt`；展示解析与索引状态，失败给可读原因
4. 对话问答：每条答案至少 1 条可点击引用（文档名 + 原文片段）
5. 权限两级：`admin` / `member`
6. Docker Compose 本机一键起 API + Web + DB + 向量组件

**明确不做**

- 多租户 / 白标 / 计费
- 钉钉、企微、飞书机器人入口
- 审批流、密级、水印、审计导出
- 图片 OCR、音视频转写、网页爬取入库
- 多模态视觉问答、Agent 工具编排
- 生产级 SSO（LDAP / OIDC）——二期再谈

边界写死是为了让首期能验收，不是遗漏。

---

## 技术栈与端口

| 层 | 默认选型 |
| --- | --- |
| 后端 | FastAPI + SQLAlchemy 2 + Pydantic 2，分层 `routes → services → repositories → models` |
| 前端 | Vite + Vue 3 + TypeScript + Vue Router + Pinia |
| 业务库 | PostgreSQL 16（本地冒烟可切 SQLite） |
| 向量库 | Qdrant（单 collection + `kb_id` 过滤；备选 pgvector） |
| 解析 | PyMuPDF + `python-docx` + 原生 md/txt |
| 切块 | 递归字符切块，`chunk_size=800` / `overlap=120`，单块上限 1200 字符 |
| Embedding | 硅基流动 `BAAI/bge-m3`（1024 维）；无 key 自动 stub |
| LLM | OpenAI 兼容网关，默认 DeepSeek `deepseek-chat`；无 key 自动 stub |
| 鉴权 | JWT（access + refresh）+ bcrypt；启动 bootstrap 管理员 |
| 设计 Token | 单一青绿强调色 `#0e7490`，石墨侧栏；SVG 图标，无 emoji |

| 服务 | 端口 | 说明 |
| --- | --- | --- |
| web（Vite dev） | **3080** | 前端；`/api`、`/healthz` 代理到 API |
| api（uvicorn） | **8088** | REST；`/healthz` 探活 |
| postgres | **5432** | 业务元数据 |
| qdrant | **6333 / 6334** | HTTP / gRPC |

端口刻意避开 8010 与 5173。

---

## 目录结构

```
企业RAG知识库/
├── AGENTS.md                      # 项目约定、PyCharm 运行配置、手启说明
├── README.md                      # 本文件
├── 01-竞品分析/                   # 占位（.gitkeep）
├── 02-产品文档/
│   └── 企业RAG_一页纸定位_v0.1.md
├── 03-技术文档/
│   ├── 企业RAG_技术选型_v0.1.md
│   ├── 企业RAG_API契约_v0.1.md
│   └── 企业RAG_openapi_v0.1.yaml
├── 04-品牌设计/                   # 占位（.gitkeep）
├── 05-UIUX设计/                   # 设计真源：5 页高保真 HTML + tokens.css + 设计说明
├── 06-项目编码/
│   ├── enterprise_rag_api/        # FastAPI：app/ + tests/ + Dockerfile + docker-compose.yml
│   └── enterprise-rag-web/        # Vue3：src/ + package.json + .env.example
├── 07-测试用例/                   # 占位（.gitkeep）
└── 08-其它文档/                   # 当前状态、project-tracker、通用型自检
```

`05-UIUX设计/` 是设计真源，**禁止在前端工程里反向修改它**。

---

## 本地跑起来

### A. 无 Docker / 无外网（推荐先跑这条）

后端用 SQLite + Embedding/LLM stub，索引状态机仍能推到 `ready`，问答返回引用结构，不依赖任何外部 API Key。

```bash
# 终端 1：API
cd 06-项目编码/enterprise_rag_api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-smoke.txt
pytest -q
cp -n .env.example .env
export DATABASE_URL=sqlite:///./enterprise_rag.db
export EMBEDDING_STUB=true LLM_STUB=true
uvicorn app.main:app --host 127.0.0.1 --port 8088

# 另开终端探活
curl -s http://127.0.0.1:8088/healthz
```

```bash
# 终端 2：Web
cd 06-项目编码/enterprise-rag-web
npm install
npm run dev          # http://localhost:3080，VITE_API_TARGET 默认 http://127.0.0.1:8088
```

登录账号取自 `.env.example` 的 `BOOTSTRAP_ADMIN_*`（示例值 `admin` / `changeme`）。**这是示例口令，不是生产凭据，部署前必须改。**
仅 Mock 模式（`VITE_USE_MOCK=true`）才用 `admin` / `admin123`、`chenke` / `member123`，两者别混。

### B. Docker Compose

```bash
cd 06-项目编码/enterprise_rag_api
cp -n .env.example .env
docker compose up --build
```

当前 Compose 能稳定起 `db` + `qdrant` + `api`；`web` 是 nginx 空页占位（`profiles: ["web"]`），**可用 UI 仍需本机 Vite**。文件已写好，需你显式执行，本仓库不会自动拉起常驻进程。

### C. PyCharm

用 PyCharm 打开**项目根目录**（不是 API 子目录），`.idea/runConfigurations/` 提供 `API FastAPI 8088`、`后台前端 3080` 和 Compound `前后端_8088_3080`。详见 `AGENTS.md`。

构建校验：`cd 06-项目编码/enterprise-rag-web && npm run build`。

---

## 关键约定

**统一响应**：`{ "code": 0, "data": {}, "message": "" }`，`code !== 0` 即业务错误；Base `http://localhost:8088`，业务前缀 `/api/v1`，鉴权 `Authorization: Bearer <token>`。

**文档状态机**：

```
uploaded → parsing → chunking → indexing → ready
                ↘ parse_failed
                           ↘ index_failed
```

失败态 `fail_reason` 必填可读原因；`parse_failed` / `index_failed` 可由管理员触发 `reindex` 回到 `parsing`。下架 / 删除会同步清理 Qdrant 点，保证后续检索不再命中。

**引用是硬要求**：成功作答 `citations` 至少 1 条（`doc_id`、`doc_name`、`chunk_id`、`snippet`、`page?`、`score?`）；无命中时 `answer` = 「知识库中未找到相关内容」、`citations` = `[]`。

**权限**：`admin` 可建库、上传、下架、删除、重索引、看成员；`member` 只能列表 / 详情只读 + 自己库内问答。归档 KB 上新建会话返回 409。

**前端硬门禁**：禁用 emoji 功能图标（用 SVG）；除 `#fff` / `#000` 外禁止硬编码色值，一律走 `var(--token)`；禁紫粉渐变、默认靛蓝 `#6366f1`、Welcome / Lorem 占位文案。

---

## 已知限制（上线前必读）

| 限制 | 现状 | 影响 |
| --- | --- | --- |
| 流式问答 | `POST …/messages:stream` 返回 **501**「流式问答尚未实现」 | 当前只有非流式问答 |
| Compose `web` | nginx 空镜像占位，非 Vue 构建产物 | 「一键起全栈」尚未成立 |
| 租户模型 | 单组织单实例，数据模型无 `org_id` / `tenant_id` | 同实例不能安全服务两家企业；换企业 = 新库 + 新 collection + 新 JWT/管理员密码 + 新 `.env` |
| 成员管理 | 仅启动 bootstrap 管理员；无注册 / 邀请 / 创建成员 / `PATCH members` | 第二个账号需补接口或运维插库 |
| 向量降级 | Qdrant 不可达时**静默**回退进程内 memory | 「库挂了仍像能问答」，但重启丢向量，运维必须知情 |
| 数据库迁移 | 无 Alembic，schema 靠 `Base.metadata.create_all` | 表结构变更需手工处理 |
| CORS | `allow_origins=["*"]` + `allow_credentials=True` | 上线前必须收紧到企业前端域 |
| Stub 语义 | 无 Embedding / LLM key 时自动 stub，索引仍能到 `ready` | 状态 `ready` **不等于**真实语义检索已生效 |
| 运维默认值 | `changeme` 类示例口令、`qdrant` 无鉴权/TLS、无迁移 job / seed 容器 / 异步索引队列 | 生产环境需逐项替换与加固 |
| 交付状态 | 未部署、无 CI、未声明 License | 复用前需与维护者确认 |

完整排查见 `08-其它文档/通用型自检_后端备注_2026-11-02.md`。

---

## 验收口径（首期过线）

- 上传 3 份样例文档后，对其中明确事实提问，答案能引用到对应片段
- 故意问库外问题，系统明确「知识库中未找到」，不胡编
- 管理员下架文档后，后续回答不再引用该文档
- `/healthz` 绿；前端 5 个主路径均可打开

---

## 文档索引

| 想看什么 | 去哪 |
| --- | --- |
| 产品边界、做/不做、验收 | `02-产品文档/企业RAG_一页纸定位_v0.1.md` |
| 选型对比与默认参数 | `03-技术文档/企业RAG_技术选型_v0.1.md` |
| 端点、错误码、状态机、引用结构 | `03-技术文档/企业RAG_API契约_v0.1.md` |
| 机器可读契约 | `03-技术文档/企业RAG_openapi_v0.1.yaml` |
| 设计 Token 与五页交互 | `05-UIUX设计/README.md`、`设计说明.md` |
| 后端启动、分层、Compose | `06-项目编码/enterprise_rag_api/README.md` |
| 前端路由、Mock 开关、硬门禁 | `06-项目编码/enterprise-rag-web/README.md` |
| 手启配置与项目约定 | `AGENTS.md` |
| 进度与状态 | `08-其它文档/当前状态.md`、`project-tracker.md` |

---

## 仓库约定

- 远程 `git@github.com:genapohub/enterprise_rag.git`，单仓库管理整个项目根目录；前后端均为普通子目录，不保留嵌套 `.git`。
- `.env`、`*.db`、`.venv/`、`node_modules/`、`dist/`、`__pycache__/`、`.idea/workspace.xml`、`.workbuddy/` 一律不入库；**`.env.example` 必须入库**。推送公开仓库前做密钥扫描。
- 密钥不写入镜像、响应或提交；示例口令仅用于本地冒烟。
- 空目录用 `.gitkeep` 保留骨架（`01`、`04`、`07`）。
- 服务需手启，AI 不代启常驻进程。
