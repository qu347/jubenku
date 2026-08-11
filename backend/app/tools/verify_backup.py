from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote


MANIFEST_VERSION = 1


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    errors: list[str]
    database_integrity: str | None = None
    alembic_version: str | None = None
    storage_file_count: int | None = None
    storage_total_size_bytes: int | None = None
    missing_referenced_file_count: int | None = None
    orphan_storage_file_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_manifest_path(root: Path, raw_path: object) -> Path:
    if not isinstance(raw_path, str) or not raw_path or ":" in raw_path or "\\" in raw_path:
        raise ValueError("manifest 包含无效相对路径")
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("manifest 包含不安全相对路径")
    resolved_root = root.resolve()
    target = resolved_root.joinpath(*relative.parts).resolve()
    try:
        target.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("manifest 路径超出备份目录") from exc
    return target


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"manifest.json 无法读取：{exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("manifest.json 顶层必须是对象")
    return payload


def _actual_storage_inventory(storage_root: Path) -> dict[str, dict[str, int | str]]:
    inventory: dict[str, dict[str, int | str]] = {}
    for path in sorted(storage_root.rglob("*")):
        if path.is_symlink():
            raise ValueError("备份 storage 中不允许存在符号链接")
        if path.is_file():
            relative = path.relative_to(storage_root).as_posix()
            inventory[relative] = {
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    return inventory


def _safe_database_storage_path(raw_path: object) -> str | None:
    if not isinstance(raw_path, str) or not raw_path or ":" in raw_path or "\\" in raw_path:
        return None
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    return relative.as_posix()


def verify_backup(
    backup_directory: Path,
    *,
    require_verified_marker: bool = True,
) -> VerificationResult:
    """Verify manifest, database integrity, and every backed-up storage file."""

    backup_root = backup_directory.expanduser().resolve()
    errors: list[str] = []
    integrity: str | None = None
    alembic_version: str | None = None
    actual_file_count: int | None = None
    actual_total_size: int | None = None
    referenced_storage_paths: set[str] | None = None
    missing_referenced_file_count: int | None = None
    orphan_storage_file_count: int | None = None

    manifest_path = backup_root / "manifest.json"
    if not backup_root.is_dir():
        return VerificationResult(False, ["备份目录不存在"])
    if not manifest_path.is_file():
        return VerificationResult(False, ["缺少 manifest.json"])
    try:
        manifest = _load_manifest(manifest_path)
    except ValueError as exc:
        return VerificationResult(False, [str(exc)])

    if manifest.get("manifest_version") != MANIFEST_VERSION:
        errors.append("manifest 版本不受支持")
    if manifest.get("status") != "complete":
        errors.append("备份未标记为 complete")
    backup_time = manifest.get("backup_time_utc")
    if not isinstance(backup_time, str):
        errors.append("manifest 缺少有效备份时间")
    else:
        try:
            parsed_backup_time = datetime.fromisoformat(backup_time.replace("Z", "+00:00"))
            if parsed_backup_time.tzinfo is None:
                raise ValueError
        except ValueError:
            errors.append("manifest 备份时间必须是带时区的 ISO 8601 格式")
    verification = manifest.get("verification")
    if require_verified_marker and (
        not isinstance(verification, dict) or verification.get("status") != "passed"
    ):
        errors.append("备份没有通过验证标记")

    database_info = manifest.get("database")
    database_path: Path | None = None
    if not isinstance(database_info, dict):
        errors.append("manifest 缺少 database 信息")
    else:
        if database_info.get("path") != "database/script_materials.db":
            errors.append("manifest 数据库路径不符合备份结构")
        try:
            database_path = _safe_manifest_path(backup_root, database_info.get("path"))
        except ValueError as exc:
            errors.append(str(exc))
        if database_path is not None:
            if not database_path.is_file():
                errors.append("备份数据库文件缺失")
            else:
                expected_size = database_info.get("size_bytes")
                if not isinstance(expected_size, int) or database_path.stat().st_size != expected_size:
                    errors.append("备份数据库大小与 manifest 不一致")
                expected_hash = database_info.get("sha256")
                try:
                    actual_database_hash = sha256_file(database_path)
                except OSError as exc:
                    errors.append(f"备份数据库无法读取：{exc}")
                    actual_database_hash = None
                if not isinstance(expected_hash, str) or actual_database_hash != expected_hash:
                    errors.append("备份数据库 SHA-256 与 manifest 不一致")
                try:
                    encoded_path = quote(database_path.as_posix(), safe="/:")
                    with sqlite3.connect(f"file:{encoded_path}?mode=ro", uri=True) as connection:
                        connection.execute("PRAGMA query_only=ON")
                        row = connection.execute("PRAGMA integrity_check").fetchone()
                        integrity = str(row[0]) if row else None
                        if integrity != "ok":
                            errors.append(f"SQLite 完整性检查失败：{integrity or '无结果'}")
                        try:
                            version_row = connection.execute(
                                "SELECT version_num FROM alembic_version LIMIT 1"
                            ).fetchone()
                            alembic_version = str(version_row[0]) if version_row else None
                        except sqlite3.DatabaseError:
                            alembic_version = None
                        try:
                            material_rows = connection.execute(
                                """
                                SELECT storage_path
                                FROM materials
                                WHERE deleted_at IS NULL
                                  AND COALESCE(storage_path, '') <> ''
                                """
                            ).fetchall()
                            referenced_storage_paths = set()
                            unsafe_reference_count = 0
                            for row in material_rows:
                                safe_path = _safe_database_storage_path(row[0])
                                if safe_path is None:
                                    unsafe_reference_count += 1
                                else:
                                    referenced_storage_paths.add(safe_path)
                            if unsafe_reference_count:
                                errors.append(
                                    f"数据库包含不安全素材相对路径：{unsafe_reference_count} 条"
                                )
                        except sqlite3.DatabaseError as exc:
                            errors.append(f"无法读取备份数据库 materials 表：{exc}")
                except sqlite3.DatabaseError as exc:
                    errors.append(f"备份数据库无法打开或已损坏：{exc}")

    storage_info = manifest.get("storage")
    if not isinstance(storage_info, dict):
        errors.append("manifest 缺少 storage 信息")
    else:
        if storage_info.get("root") != "storage/materials":
            errors.append("manifest 素材目录路径不符合备份结构")
        try:
            storage_root = _safe_manifest_path(backup_root, storage_info.get("root"))
        except ValueError as exc:
            errors.append(str(exc))
            storage_root = None
        if storage_root is not None:
            if not storage_root.is_dir():
                errors.append("备份 storage/materials 目录缺失")
            else:
                try:
                    actual_inventory = _actual_storage_inventory(storage_root)
                except (OSError, ValueError) as exc:
                    errors.append(f"备份 storage 无法校验：{exc}")
                    actual_inventory = {}
                actual_file_count = len(actual_inventory)
                actual_total_size = sum(int(item["size_bytes"]) for item in actual_inventory.values())
                if storage_info.get("file_count") != actual_file_count:
                    errors.append("storage 文件数量与 manifest 不一致")
                if storage_info.get("total_size_bytes") != actual_total_size:
                    errors.append("storage 文件总大小与 manifest 不一致")

                manifest_files = storage_info.get("files")
                expected_inventory: dict[str, dict[str, int | str]] = {}
                if not isinstance(manifest_files, list):
                    errors.append("manifest storage.files 必须是数组")
                else:
                    for item in manifest_files:
                        if not isinstance(item, dict):
                            errors.append("manifest storage.files 包含无效条目")
                            continue
                        raw_path = item.get("path")
                        try:
                            _safe_manifest_path(storage_root, raw_path)
                        except ValueError as exc:
                            errors.append(str(exc))
                            continue
                        if raw_path in expected_inventory:
                            errors.append(f"manifest storage.files 路径重复：{raw_path}")
                            continue
                        expected_inventory[str(raw_path)] = {
                            "size_bytes": item.get("size_bytes"),
                            "sha256": item.get("sha256"),
                        }
                    if expected_inventory != actual_inventory:
                        errors.append("storage 文件清单或内容校验与 manifest 不一致")
                if referenced_storage_paths is not None:
                    actual_paths = set(actual_inventory)
                    missing_referenced_file_count = len(referenced_storage_paths - actual_paths)
                    orphan_storage_file_count = len(actual_paths - referenced_storage_paths)
                    if missing_referenced_file_count:
                        errors.append(
                            "备份数据库引用的素材文件缺失："
                            f"{missing_referenced_file_count} 个"
                        )

    return VerificationResult(
        valid=not errors,
        errors=errors,
        database_integrity=integrity,
        alembic_version=alembic_version,
        storage_file_count=actual_file_count,
        storage_total_size_bytes=actual_total_size,
        missing_referenced_file_count=missing_referenced_file_count,
        orphan_storage_file_count=orphan_storage_file_count,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="验证数据库与素材文件备份的一致性")
    parser.add_argument("backup_directory", type=Path, help="待验证的时间戳备份目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出验证结果")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = verify_backup(args.backup_directory)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.valid:
        print("备份验证成功")
        print(f"SQLite 完整性：{result.database_integrity}")
        print(f"Alembic 版本：{result.alembic_version or '未记录'}")
        print(f"素材文件数：{result.storage_file_count}")
        print(f"素材总大小：{result.storage_total_size_bytes} 字节")
        print(f"数据库引用缺失文件数：{result.missing_referenced_file_count}")
        print(f"孤立素材文件数：{result.orphan_storage_file_count}")
    else:
        print("备份验证失败")
        for error in result.errors:
            print(f"- {error}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
