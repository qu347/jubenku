import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Test collection must be safe even when pytest is launched from a terminal
# that previously ran production or restore commands. Clear every path-bearing
# production override before importing app.main, which constructs the global
# FastAPI application and database engine.
for variable_name in (
    "SETTINGS_ENV_FILE",
    "DATABASE_URL",
    "STORAGE_ROOT",
    "MATERIAL_STORAGE_PATH",
    "LOG_DIR",
    "BACKUP_ROOT",
    "TEMP_ROOT",
    "FRONTEND_DIST",
    "CORS_ALLOWED_ORIGINS",
):
    os.environ.pop(variable_name, None)
os.environ["APP_ENV"] = "test"
os.environ["SERVE_FRONTEND"] = "false"
test_import_runtime = Path(__file__).resolve().parents[2] / ".runtime" / "pytest_import_guard"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["STORAGE_ROOT"] = str(test_import_runtime / "storage")
os.environ["MATERIAL_STORAGE_PATH"] = str(test_import_runtime / "storage" / "materials")
os.environ["LOG_DIR"] = str(test_import_runtime / "logs")
os.environ["BACKUP_ROOT"] = str(test_import_runtime / "backups")
os.environ["TEMP_ROOT"] = str(test_import_runtime / "temp")
os.environ["FRONTEND_DIST"] = str(test_import_runtime / "dist")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import models  # noqa: E402,F401
from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import settings  # noqa: E402


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def upload_storage_path(tmp_path: Path) -> Path:
    path = tmp_path / "materials"
    path.mkdir()
    return path


@pytest.fixture()
def client(
    db_session: Session,
    upload_storage_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    def override_db():
        yield db_session

    monkeypatch.setattr(settings, "material_storage_path", upload_storage_path)
    monkeypatch.setattr(settings, "max_upload_mb", 100)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
