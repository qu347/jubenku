from __future__ import annotations

import asyncio
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from app.api.endpoints.health import _migration_head
from app.core.config import Settings, settings
from app.core.logging import get_app_logger
from app.core.runtime import RuntimeConfigurationError, prepare_runtime_directories
from app.database.session import build_engine, get_db
from app.database.base import Base
from app.main import create_application
from app.models import Material
from app.services.material_service import MaterialService


@pytest.fixture()
def runtime_tmp_path(tmp_path: Path) -> Generator[Path, None, None]:
    path = tmp_path / "runtime"
    path.mkdir()
    try:
        yield path
    finally:
        logger = get_app_logger()
        for handler in list(logger.handlers):
            if getattr(handler, "_script_materials_handler", False):
                logger.removeHandler(handler)
                handler.close()


def _runtime_settings(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "production",
        "database_url": f"sqlite:///{(tmp_path / 'database' / 'app.db').as_posix()}",
        "storage_root": tmp_path / "storage",
        "log_dir": tmp_path / "logs",
        "backup_root": tmp_path / "backups",
        "temp_root": tmp_path / "temp",
        "serve_frontend": False,
    }
    values.update(overrides)
    return Settings(**values)


def _ready_session() -> tuple[Session, object]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
    session.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
        {"version": _migration_head()},
    )
    session.commit()
    return session, engine


def test_pytest_import_guard_never_uses_inherited_production_settings() -> None:
    expected_runtime = Path(__file__).resolve().parents[2] / ".runtime" / "pytest_import_guard"
    assert settings.app_env == "test"
    assert settings.is_production is False
    assert settings.serve_frontend is False
    assert settings.database_url == "sqlite:///:memory:"
    assert settings.storage_root.resolve() == (expected_runtime / "storage").resolve()
    assert settings.material_storage_path.resolve() == (
        expected_runtime / "storage" / "materials"
    ).resolve()
    assert settings.log_dir.resolve() == (expected_runtime / "logs").resolve()
    assert settings.backup_root.resolve() == (expected_runtime / "backups").resolve()
    assert settings.temp_root.resolve() == (expected_runtime / "temp").resolve()
    assert "script_material_data" not in settings.database_url
    assert "script_material_data" not in str(settings.storage_root)


def test_production_settings_read_selected_env_file(
    runtime_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path = runtime_tmp_path
    env_file = tmp_path / ".env.production"
    env_file.write_text(
        "\n".join(
            (
                "APP_ENV=production",
                "APP_HOST=0.0.0.0",
                "APP_PORT=8123",
                f"DATABASE_URL=sqlite:///{(tmp_path / 'database' / 'prod.db').as_posix()}",
                f"STORAGE_ROOT={(tmp_path / 'storage').as_posix()}",
                f"LOG_DIR={(tmp_path / 'logs').as_posix()}",
                f"BACKUP_ROOT={(tmp_path / 'backups').as_posix()}",
                f"TEMP_ROOT={(tmp_path / 'temp').as_posix()}",
                "SERVE_FRONTEND=false",
            )
        ),
        encoding="utf-8",
    )
    for variable_name in (
        "DATABASE_URL",
        "STORAGE_ROOT",
        "MATERIAL_STORAGE_PATH",
        "LOG_DIR",
        "BACKUP_ROOT",
        "TEMP_ROOT",
        "FRONTEND_DIST",
    ):
        monkeypatch.delenv(variable_name, raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SETTINGS_ENV_FILE", str(env_file))

    config = Settings()

    assert config.is_production is True
    assert config.app_host == "0.0.0.0"
    assert config.app_port == 8123
    assert config.database_url.endswith("/database/prod.db")
    assert config.storage_root == tmp_path / "storage"
    assert config.material_storage_path == tmp_path / "storage" / "materials"
    assert config.cors_origin_list == []


def test_prepare_runtime_creates_all_production_directories(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    config = _runtime_settings(tmp_path)

    prepare_runtime_directories(config)

    assert (tmp_path / "database").is_dir()
    assert config.storage_root.is_dir()
    assert config.material_storage_path.is_dir()
    assert config.log_dir.is_dir()
    assert config.backup_root.is_dir()
    assert config.temp_root.is_dir()


def test_production_material_path_cannot_escape_storage_root(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    config = _runtime_settings(
        tmp_path,
        material_storage_path=tmp_path / "outside-production-storage",
    )

    assert config.material_storage_path == config.storage_root / "materials"


def test_production_start_fails_when_frontend_dist_is_missing(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    config = _runtime_settings(
        tmp_path,
        serve_frontend=True,
        frontend_dist=tmp_path / "missing-dist",
    )

    with pytest.raises(RuntimeConfigurationError, match="index.html"):
        create_application(config)


def test_fastapi_serves_assets_spa_fallback_and_api_404(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text("<html>SPRINT4-SPA</html>", encoding="utf-8")
    (assets / "app.js").write_text("window.sprint4=true", encoding="utf-8")
    config = Settings(app_env="test", serve_frontend=True, frontend_dist=dist)
    application = create_application(config)

    with TestClient(application) as client:
        asset_response = client.get("/assets/app.js")
        spa_response = client.get("/materials")
        api_response = client.get("/api/route-that-does-not-exist")
        wrong_method_response = client.post("/api/health")

    assert asset_response.status_code == 200
    assert asset_response.text == "window.sprint4=true"
    assert "immutable" in asset_response.headers["cache-control"]
    assert spa_response.status_code == 200
    assert "SPRINT4-SPA" in spa_response.text
    assert spa_response.headers["cache-control"] == "no-store, max-age=0"
    assert api_response.status_code == 404
    assert api_response.json()["error"]["code"] == "api_not_found"
    assert "SPRINT4-SPA" not in api_response.text
    assert wrong_method_response.status_code == 405
    assert wrong_method_response.json()["error"]["code"] == "method_not_allowed"
    assert wrong_method_response.headers["allow"] == "GET"
    assert "SPRINT4-SPA" not in wrong_method_response.text


def test_readiness_checks_database_migration_storage_and_frontend(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    material_storage = tmp_path / "storage" / "materials"
    material_storage.mkdir(parents=True)
    config = Settings(
        app_env="test",
        storage_root=tmp_path / "storage",
        material_storage_path=material_storage,
        serve_frontend=False,
    )
    application = create_application(config)
    session, engine = _ready_session()

    def override_db() -> Generator[Session, None, None]:
        yield session

    application.dependency_overrides[get_db] = override_db
    try:
        with TestClient(application) as client:
            response = client.get("/api/health/ready")
    finally:
        session.close()
        engine.dispose()  # type: ignore[union-attr]

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"status", "database", "migration", "storage", "frontend", "timestamp"}
    assert payload["status"] == "ready"
    assert payload["database"] == "ok"
    assert payload["migration"] == "ok"
    assert payload["storage"] == "ok"
    assert payload["frontend"] == "disabled"
    assert str(tmp_path) not in response.text


def test_readiness_reports_unwritable_storage_without_exposing_path(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    not_a_directory = tmp_path / "storage-file"
    not_a_directory.write_text("blocked", encoding="utf-8")
    config = Settings(
        app_env="test",
        material_storage_path=not_a_directory,
        serve_frontend=False,
    )
    application = create_application(config)
    session, engine = _ready_session()

    def override_db() -> Generator[Session, None, None]:
        yield session

    application.dependency_overrides[get_db] = override_db
    try:
        with TestClient(application) as client:
            response = client.get("/api/health/ready")
    finally:
        session.close()
        engine.dispose()  # type: ignore[union-attr]

    assert response.status_code == 503
    assert response.json()["storage"] == "error"
    assert str(not_a_directory) not in response.text


def test_sqlite_connections_enable_foreign_keys_busy_timeout_and_wal(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    database_path = tmp_path / "pragmas.db"
    engine = build_engine(
        f"sqlite:///{database_path.as_posix()}",
        busy_timeout_ms=4321,
        enable_wal=True,
    )
    try:
        with engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            assert connection.execute(text("PRAGMA busy_timeout")).scalar_one() == 4321
            assert connection.execute(text("PRAGMA journal_mode")).scalar_one().lower() == "wal"
    finally:
        engine.dispose()


def test_concurrent_uploads_keep_sqlite_and_storage_consistent(runtime_tmp_path: Path) -> None:
    database_path = runtime_tmp_path / "concurrent.db"
    storage_path = runtime_tmp_path / "storage" / "materials"
    engine = build_engine(
        f"sqlite:///{database_path.as_posix()}",
        busy_timeout_ms=10_000,
        enable_wal=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def upload(index: int) -> dict[str, object]:
        session = session_factory()
        upload_file = UploadFile(
            io.BytesIO(f"并发素材 {index}".encode("utf-8")),
            filename=f"concurrent-{index}.txt",
            headers=Headers({"content-type": "text/plain"}),
        )
        try:
            return asyncio.run(
                MaterialService(session, storage_root=storage_path).upload(
                    files=[upload_file],
                    genre_module_id=None,
                    material_type="参考资料",
                    tags=[],
                    source="concurrency-test",
                    description="",
                    upload_platform="番茄小说",
                    platform_heat=80,
                )
            )
        finally:
            session.close()

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(upload, range(5)))
        assert all(result["success_count"] == 1 for result in results), results
        with session_factory() as verification_session:
            assert verification_session.scalar(select(func.count(Material.id))) == 5
            assert verification_session.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
        assert len(list(storage_path.rglob("*.txt"))) == 5
        assert not list(storage_path.rglob("*.part"))
    finally:
        engine.dispose()


def test_production_error_response_never_contains_traceback(runtime_tmp_path: Path) -> None:
    tmp_path = runtime_tmp_path
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    config = _runtime_settings(tmp_path, frontend_dist=dist)
    application = create_application(config)

    @application.get("/api/test-unhandled-error")
    def fail() -> None:
        raise RuntimeError("server-only-secret")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/api/test-unhandled-error")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "server-only-secret" not in response.text
    assert "Traceback" not in response.text
    assert (config.log_dir / "application.log").is_file()
    assert (config.log_dir / "error.log").is_file()
