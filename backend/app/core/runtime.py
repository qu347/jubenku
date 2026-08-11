from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import make_url

from app.core.config import Settings


class RuntimeConfigurationError(RuntimeError):
    """Raised before serving requests when production paths are unusable."""


def sqlite_database_path(database_url: str) -> Path | None:
    """Return the configured SQLite file without exposing it to API callers."""

    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return None
    return Path(url.database).expanduser()


def _ensure_writable_directory(path: Path, label: str) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            raise NotADirectoryError(str(path))
        probe = path / f".write-probe-{os.getpid()}-{uuid4().hex}"
        probe.write_bytes(b"")
        probe.unlink()
    except OSError as exc:
        raise RuntimeConfigurationError(f"生产环境{label}不可创建或不可写") from exc


def prepare_runtime_directories(config: Settings) -> None:
    """Create and validate all production data directories.

    This is intentionally called only during application construction in
    production mode, so importing tests or development tools cannot touch the
    formal production data root by accident.
    """

    database_path = sqlite_database_path(config.database_url)
    directories: list[tuple[Path, str]] = [
        (config.storage_root, "存储根目录"),
        (config.material_storage_path, "素材存储目录"),
        (config.backup_root, "备份目录"),
        (config.log_dir, "日志目录"),
        (config.temp_root, "临时目录"),
    ]
    if database_path is not None:
        directories.insert(0, (database_path.parent, "数据库目录"))

    checked: set[Path] = set()
    for path, label in directories:
        resolved = path.resolve()
        if resolved in checked:
            continue
        checked.add(resolved)
        _ensure_writable_directory(path, label)


def validate_frontend_dist(config: Settings) -> Path:
    dist = config.frontend_dist.expanduser().resolve()
    if not dist.is_dir() or not (dist / "index.html").is_file():
        raise RuntimeConfigurationError("前端生产构建目录不存在或缺少 index.html")
    return dist
