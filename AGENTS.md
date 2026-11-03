# 企业RAG知识库 · 项目层 AGENTS

- 产品名：企业 RAG 知识库（单组织 Web 问答 MVP）
- 拍板：2026-11-02；设计先行；选型默认已锁定
- 协作：全局真源见 `../agents.md`；本文件只放项目差异
- 本地服务端口：web **3080** · api **8088** · postgres **5432** · qdrant **6333/6334**（见 `03-技术文档/企业RAG_技术选型_v0.1.md`）；勿擅自 nohup/后台常驻起服务，Compose 文件在 `06-项目编码/enterprise_rag_api/`
- 契约：`03-技术文档/企业RAG_API契约_v0.1.md` · OpenAPI 同目录
- 交付：路径 + 改了啥 + 怎么验 + 没做完

## PyCharm 手启

### 整项目根打开（推荐 · 必须开根目录）

> **常见踩坑**：若 Run 列表里只有「API FastAPI 8088」、没有「后台前端 3080」，说明当前打开的是 `06-项目编码/enterprise_rag_api/` 子目录，不是项目根。请 File → Close Project 后重新 Open 根目录 `企业RAG知识库/`。


用 PyCharm 打开本目录（`企业RAG知识库/`，不要只开子目录），运行配置在 `.idea/runConfigurations/`：

| 配置名 | 作用 | 探活 |
| --- | --- | --- |
| `API FastAPI 8088` | `uvicorn app.main:app --host 127.0.0.1 --port 8088 --reload`；工作目录 `06-项目编码/enterprise_rag_api`；加载该目录 `.env`；冒烟默认 `DATABASE_URL=sqlite:///./enterprise_rag.db` + `EMBEDDING_STUB`/`LLM_STUB=true` | http://127.0.0.1:8088/healthz |
| `后台前端 3080` | `npm run dev`（`06-项目编码/enterprise-rag-web`；`node-interpreter=/usr/local/bin/node`；env `VITE_API_TARGET=http://127.0.0.1:8088`、`VITE_USE_MOCK=false`） | http://localhost:3080 |
| `前后端_8088_3080` | Compound：组合 `API FastAPI 8088` + `后台前端 3080` | 先 healthz，再 http://localhost:3080 |

解释器名：`enterprise_rag_api/.venv`（`SDK_HOME` → `06-项目编码/enterprise_rag_api/.venv/bin/python`）。可分别点运行，或一次点 Compound；**AI 不代启常驻**。前端 Vite 代理目标：`http://127.0.0.1:8088`。

### 只打开 API 子目录

若只打开 `06-项目编码/enterprise_rag_api/`，同名配置在该目录 `.idea/runConfigurations/API_FastAPI_8088.xml`（`$PROJECT_DIR$` = API 根；工作目录/`.env`/`.venv` 均相对该目录）。解释器同样选 `enterprise_rag_api/.venv`。

