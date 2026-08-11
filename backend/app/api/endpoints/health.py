from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import BACKEND_ROOT, Settings
from app.core.logging import get_app_logger
from app.database.session import get_db
from app.schemas.common import ApiResponse

router = APIRouter(tags=["health"])
logger = get_app_logger("health")


class ReadinessData(BaseModel):
    status: Literal["ready", "not_ready"]
    database: Literal["ok", "error"]
    migration: Literal["ok", "outdated", "error"]
    storage: Literal["ok", "error"]
    frontend: Literal["ok", "disabled", "error"]
    timestamp: datetime


@lru_cache(maxsize=1)
def _migration_head() -> str:
    alembic_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_config.set_main_option("script_location", (BACKEND_ROOT / "alembic").as_posix())
    head = ScriptDirectory.from_config(alembic_config).get_current_head()
    if head is None:
        raise RuntimeError("Alembic head is unavailable")
    return head


def _storage_writable(path: Path) -> bool:
    if not path.is_dir():
        return False
    probe = path / f".readiness-{uuid4().hex}"
    try:
        probe.write_bytes(b"")
        probe.unlink()
        return True
    except OSError:
        try:
            probe.unlink(missing_ok=True)
        except OSError:
            pass
        return False


@router.get("/health", response_model=ApiResponse[dict[str, str]])
def health_check() -> dict[str, Any]:
    return {"success": True, "data": {"status": "ok"}, "message": "服务运行正常"}


@router.get(
    "/health/ready",
    response_model=ReadinessData,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessData}},
)
def readiness_check(
    request: Request,
    response: Response,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    config: Settings = request.app.state.settings
    checks: dict[str, str] = {
        "database": "error",
        "migration": "error",
        "storage": "error",
        "frontend": "disabled" if not config.serve_frontend else "error",
    }

    try:
        session.execute(text("SELECT 1")).scalar_one()
        checks["database"] = "ok"
    except Exception as exc:
        logger.warning("readiness_database_failed type=%s", type(exc).__name__)

    if checks["database"] == "ok":
        try:
            current = session.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            checks["migration"] = "ok" if current == _migration_head() else "outdated"
        except Exception as exc:
            logger.warning("readiness_migration_failed type=%s", type(exc).__name__)

    checks["storage"] = "ok" if _storage_writable(config.material_storage_path) else "error"
    if config.serve_frontend:
        checks["frontend"] = (
            "ok"
            if config.frontend_dist.is_dir() and (config.frontend_dist / "index.html").is_file()
            else "error"
        )

    is_ready = all(
        (
            checks["database"] == "ok",
            checks["migration"] == "ok",
            checks["storage"] == "ok",
            checks["frontend"] in {"ok", "disabled"},
        )
    )
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    data = {
        "status": "ready" if is_ready else "not_ready",
        **checks,
        "timestamp": datetime.now(timezone.utc),
    }
    return data
