from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.tools.audit_data import sqlite_database_path
from app.tools.verify_backup import MANIFEST_VERSION, sha256_file, verify_backup


BACKUP_DIRECTORY_PATTERN = re.compile(r"^\d{8}_\d{6}(?:_\d+)?$")


@dataclass(frozen=True)
class BackupResult:
    backup_directory: Path
    manifest_path: Path
    database_sha256: str
    storage_file_count: int
    storage_total_size_bytes: int
    deleted_expired_backups: tuple[Path, ...]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalized_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _unique_destination(backup_root: Path, when: datetime) -> Path:
    stem = when.strftime("%Y%m%d_%H%M%S")
    destination = backup_root / stem
    suffix = 1
    while destination.exists():
        destination = backup_root / f"{stem}_{suffix:02d}"
        suffix += 1
    return destination


def _write_log(log_path: Path, message: str, *, when: datetime | None = None) -> None:
    timestamp = _normalized_utc(when or _utc_now()).isoformat()
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} {message}\n")


def _sqlite_backup(source_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=False)
    encoded_source = quote(source_path.as_posix(), safe="/:")
    source_uri = f"file:{encoded_source}?mode=ro"
    with sqlite3.connect(source_uri, uri=True, timeout=30) as source:
        with sqlite3.connect(destination_path, timeout=30) as destination:
            source.backup(destination)
            destination.commit()
            integrity_row = destination.execute("PRAGMA integrity_check").fetchone()
            if not integrity_row or integrity_row[0] != "ok":
                raise sqlite3.DatabaseError(
                    f"SQLite 备份完整性检查失败：{integrity_row[0] if integrity_row else '无结果'}"
                )


def _storage_manifest(storage_root: Path) -> dict[str, Any]:
    files: list[dict[str, int | str]] = []
    total_size = 0
    for path in sorted(storage_root.rglob("*")):
        if path.is_symlink():
            raise ValueError("素材目录中不允许存在符号链接")
        if path.is_file():
            size = path.stat().st_size
            total_size += size
            files.append(
                {
                    "path": path.relative_to(storage_root).as_posix(),
                    "size_bytes": size,
                    "sha256": sha256_file(path),
                }
            )
    return {
        "root": "storage/materials",
        "file_count": len(files),
        "total_size_bytes": total_size,
        "files": files,
    }


def _load_completed_manifest(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("status") != "complete":
        return None
    verification = payload.get("verification")
    if not isinstance(verification, dict) or verification.get("status") != "passed":
        return None
    return payload


def _parse_manifest_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _normalized_utc(parsed)


def cleanup_expired_backups(
    backup_root: Path,
    *,
    retention_days: int,
    verified_backup: Path,
    now: datetime | None = None,
) -> list[Path]:
    """Delete only expired, successfully verified backups after a new valid backup exists."""

    if retention_days < 1:
        raise ValueError("备份保留天数必须大于 0")
    resolved_root = backup_root.expanduser().resolve()
    protected = verified_backup.expanduser().resolve()
    try:
        protected.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("新备份目录不在 BACKUP_ROOT 内") from exc
    if not verify_backup(protected).valid:
        return []

    cutoff = _normalized_utc(now or _utc_now()) - timedelta(days=retention_days)
    deleted: list[Path] = []
    for candidate in sorted(resolved_root.iterdir()):
        if not candidate.is_dir() or candidate.resolve() == protected:
            continue
        if not BACKUP_DIRECTORY_PATTERN.fullmatch(candidate.name):
            continue
        manifest = _load_completed_manifest(candidate)
        backup_time = _parse_manifest_time(manifest.get("backup_time_utc")) if manifest else None
        if backup_time is None or backup_time >= cutoff:
            continue
        resolved_candidate = candidate.resolve()
        try:
            resolved_candidate.relative_to(resolved_root)
        except ValueError:
            continue
        shutil.rmtree(resolved_candidate)
        deleted.append(resolved_candidate)
    return deleted


def create_backup(
    *,
    database_path: Path,
    materials_root: Path,
    backup_root: Path,
    retention_days: int = 30,
    now: datetime | None = None,
) -> BackupResult:
    """Create, verify, publish, then apply retention to a consistent SQLite backup."""

    started_at = _normalized_utc(now or _utc_now())
    source_database = database_path.expanduser().resolve()
    source_storage = materials_root.expanduser().resolve()
    destination_root = backup_root.expanduser().resolve()
    if not source_database.is_file():
        raise FileNotFoundError(f"SQLite 数据库不存在：{source_database}")
    if not source_storage.is_dir():
        raise FileNotFoundError(f"素材目录不存在：{source_storage}")
    if retention_days < 1:
        raise ValueError("备份保留天数必须大于 0")
    try:
        destination_root.relative_to(source_storage)
    except ValueError:
        pass
    else:
        raise ValueError("BACKUP_ROOT 不能位于素材目录内部")
    if any(path.is_symlink() for path in source_storage.rglob("*")):
        raise ValueError("素材目录中不允许存在符号链接")

    destination_root.mkdir(parents=True, exist_ok=True)
    final_directory = _unique_destination(destination_root, started_at)
    final_directory.mkdir(parents=False, exist_ok=False)
    log_path = final_directory / "backup.log"
    manifest_path = final_directory / "manifest.json"
    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "status": "incomplete",
        "backup_time_utc": started_at.isoformat(),
        "database": None,
        "storage": None,
        "verification": {"status": "pending", "verified_at_utc": None},
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    try:
        _write_log(log_path, "开始创建一致性数据库备份", when=started_at)
        backup_database = final_directory / "database" / "script_materials.db"
        _sqlite_backup(source_database, backup_database)
        _write_log(log_path, "SQLite Backup API 备份完成")

        backup_storage = final_directory / "storage" / "materials"
        backup_storage.parent.mkdir(parents=True, exist_ok=False)
        shutil.copytree(source_storage, backup_storage, copy_function=shutil.copy2)
        _write_log(log_path, "素材文件复制完成")

        database_size = backup_database.stat().st_size
        database_hash = sha256_file(backup_database)
        storage_info = _storage_manifest(backup_storage)
        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "status": "complete",
            "backup_time_utc": started_at.isoformat(),
            "database": {
                "path": "database/script_materials.db",
                "size_bytes": database_size,
                "sha256": database_hash,
            },
            "storage": storage_info,
            "verification": {"status": "pending", "verified_at_utc": None},
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        preliminary = verify_backup(final_directory, require_verified_marker=False)
        if not preliminary.valid:
            raise RuntimeError("备份验证失败：" + "；".join(preliminary.errors))
        manifest["verification"] = {
            "status": "passed",
            "verified_at_utc": _utc_now().isoformat(),
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        final_verification = verify_backup(final_directory)
        if not final_verification.valid:
            raise RuntimeError("备份最终验证失败：" + "；".join(final_verification.errors))
        _write_log(log_path, "备份内容验证通过")

        try:
            deleted_backups = cleanup_expired_backups(
                destination_root,
                retention_days=retention_days,
                verified_backup=final_directory,
                now=started_at,
            )
        except OSError as exc:
            # A locked historical directory must not invalidate the new,
            # already verified recovery point. Operators can retry retention.
            deleted_backups = []
            _write_log(log_path, f"过期备份清理失败：{type(exc).__name__}")
        _write_log(
            final_directory / "backup.log",
            f"备份成功；清理过期备份 {len(deleted_backups)} 个",
        )
        return BackupResult(
            backup_directory=final_directory,
            manifest_path=manifest_path,
            database_sha256=database_hash,
            storage_file_count=int(storage_info["file_count"]),
            storage_total_size_bytes=int(storage_info["total_size_bytes"]),
            deleted_expired_backups=tuple(deleted_backups),
        )
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["verification"] = {"status": "failed", "verified_at_utc": None}
        manifest["failure_type"] = type(exc).__name__
        try:
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _write_log(log_path, f"备份失败：{type(exc).__name__}")
        except OSError:
            pass
        raise


def _default_materials_root(settings: object) -> Path:
    material_storage_path = getattr(settings, "material_storage_path", None)
    if material_storage_path is not None:
        return Path(material_storage_path)
    return Path(getattr(settings, "storage_root")) / "materials"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="创建数据库与素材文件的一致性备份")
    parser.add_argument("--database-url", help="覆盖环境配置中的 DATABASE_URL")
    parser.add_argument("--materials-root", type=Path, help="覆盖素材文件根目录")
    parser.add_argument("--backup-root", type=Path, help="覆盖备份根目录")
    parser.add_argument("--retention-days", type=int, help="覆盖备份保留天数")
    return parser


def main(argv: list[str] | None = None) -> int:
    from app.core.config import get_settings

    args = _build_parser().parse_args(argv)
    settings = get_settings()
    database_path = sqlite_database_path(args.database_url or settings.database_url)
    materials_root = args.materials_root or _default_materials_root(settings)
    backup_root = args.backup_root or Path(getattr(settings, "backup_root"))
    retention_days = (
        args.retention_days
        if args.retention_days is not None
        else int(getattr(settings, "backup_retention_days", 30))
    )
    try:
        result = create_backup(
            database_path=database_path,
            materials_root=materials_root,
            backup_root=backup_root,
            retention_days=retention_days,
        )
    except (FileNotFoundError, OSError, RuntimeError, sqlite3.DatabaseError, ValueError) as exc:
        print(f"备份失败：{exc}")
        return 1
    print("备份成功")
    print(f"备份目录：{result.backup_directory}")
    print(f"素材文件数：{result.storage_file_count}")
    print(f"素材总大小：{result.storage_total_size_bytes} 字节")
    print(f"数据库 SHA-256：{result.database_sha256}")
    print(f"清理过期备份：{len(result.deleted_expired_backups)} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
