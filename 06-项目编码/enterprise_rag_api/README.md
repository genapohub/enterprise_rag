# 企业 RAG 知识库 · API（MVP 骨架）

场景：单组织 Web RAG；JWT；知识库/文档状态机/对话引用；Compose 可起。

## 栈

FastAPI · Postgres（测试可用 SQLite）· Qdrant（无服务时内存向量 stub）· Embedding/LLM 无 key 自动 stub。

端口（对齐选型）：API **8088** · Postgres **5432** · Qdrant **6333** · Web **3080**（compose profile `web` 占位）。

## 本地冒烟（无需 Docker / 外网）

> 建议 **Python 3.12/3.13**。若本机仅有 3.14，用 `requirements-smoke.txt`（未钉版本，优先 wheel）；Compose 镜像固定 3.12。

```bash
cd enterprise_rag_api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-smoke.txt   # 推荐：sqlite stub 冒烟，无编译重依赖
# 全量: pip install -r requirements-dev.txt
# Compose/Postgres: pip install -r requirements-postgres.txt
pytest -q
```

## 起 API（前台，勿 nohup）

```bash
cp .env.example .env   # 按需改；勿提交真密钥
export DATABASE_URL=sqlite:///./enterprise_rag.db
export EMBEDDING_STUB=true LLM_STUB=true
uvicorn app.main:app --host 0.0.0.0 --port 8088
# 另开终端：curl -s http://127.0.0.1:8088/healthz
```

默认管理员：`.env.example` 中 `BOOTSTRAP_ADMIN_USER/PASSWORD`（示例值，生产务必改）。

## Compose（文件已写好；需你本机显式 `docker compose up`，本任务不后台拉起）

```bash
cp .env.example .env
docker compose up --build
# Web 占位：docker compose --profile web up
```

无 `EMBEDDING_API_KEY` / `LLM_API_KEY` 时走 stub：索引状态机仍可到 `ready`，问答返回 citations 结构。

## 分层

`routes` → `services` → `repositories` → `models`；统一响应 `{code,data,message}`。

## 契约

见 `../03-技术文档/企业RAG_API契约_v0.1.md` 与 `企业RAG_openapi_v0.1.yaml`。

## 不做

多租户、机器人、SSO、OCR；不 git push；不把密钥写入响应或仓库。
