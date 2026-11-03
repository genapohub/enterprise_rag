"""FastAPI entry: enterprise RAG API."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import get_settings
from app.database import init_db, SessionLocal
from app.exceptions import AppError
from app.response import fail
from app.middleware.logging_mw import RequestLogMiddleware
from app.services.auth_service import AuthService
from app.routes import health, auth, knowledge_bases, documents, conversations, members

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    init_db()
    db = SessionLocal()
    try:
        AuthService(db).ensure_bootstrap_admin()
    finally:
        db.close()
    logger.info("app started version=%s embedding_stub=%s llm_stub=%s", settings.app_version, settings.use_embedding_stub(), settings.use_llm_stub())
    yield


app = FastAPI(title="企业 RAG 知识库 API", version=get_settings().app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLogMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(knowledge_bases.router)
app.include_router(documents.router)
app.include_router(conversations.router)
app.include_router(members.router)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return fail(exc.code, exc.message, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError):
    return fail(40001, "参数校验失败", data=exc.errors(), status_code=400)


@app.exception_handler(StarletteHTTPException)
async def http_handler(_request: Request, exc: StarletteHTTPException):
    code = {401: 40101, 403: 40301, 404: 40401, 409: 40901, 429: 42901}.get(exc.status_code, 50001)
    detail = exc.detail if isinstance(exc.detail, str) else "请求失败"
    return fail(code, detail, status_code=exc.status_code)


@app.exception_handler(Exception)
async def unhandled_handler(_request: Request, exc: Exception):
    logger.exception("unhandled error: %s", exc)
    return fail(50001, "服务器内部错误", status_code=500)
