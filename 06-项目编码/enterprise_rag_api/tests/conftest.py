import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Force sqlite + stubs before app import
os.environ["DATABASE_URL"] = "sqlite:///./pytest_enterprise_rag.db"
os.environ["EMBEDDING_STUB"] = "true"
os.environ["LLM_STUB"] = "true"
os.environ["JWT_SECRET"] = "test-secret-not-for-prod"
os.environ["BOOTSTRAP_ADMIN_USER"] = "admin"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "changeme"
os.environ["UPLOAD_DIR"] = str(ROOT / "uploads_test")

# clear settings cache if any
from app.config import get_settings

get_settings.cache_clear()

db_file = ROOT / "pytest_enterprise_rag.db"
if db_file.exists():
    db_file.unlink()

from app.database import init_db, SessionLocal, Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402
from app.services.vector_store import _MEMORY  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    init_db()
    _MEMORY._points.clear()
    db = SessionLocal()
    try:
        AuthService(db).ensure_bootstrap_admin()
    finally:
        db.close()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    _MEMORY._points.clear()


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "changeme"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    return body["data"]["access_token"]


@pytest.fixture()
def auth_header(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}
