import logging
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.response import ok
from app.config import get_settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthz(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        logger.exception("health db check failed")
        db_status = "error"
        return ok({"status": "degraded", "db": db_status, "version": get_settings().app_version}, message=str(exc)[:120])
    return ok({"status": "ok", "db": db_status, "version": get_settings().app_version})
