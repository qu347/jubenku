from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from sqlalchemy.engine import make_url


@dataclass(frozen=True)
class AuditReport:
    """Read-only summary of database records and material storage consistency."""

    material_count: int
    attachment_material_count: int
    legacy_without_attachment_count: int
    missing_attachment_file_count: int
    orphan_file_count: int
    genre_metric_count: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def sqlite_database_path(database_url: str, *, base_dir: Path | None = None) -> Path:
    """Resolve a file-backed SQLite URL without opening or creating the database."""

    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        raise ValueError("数据审计和备份工具当前仅支持 SQLite 数据库")
    if not url.database or url.database == ":memory:":
        raise ValueError("数据审计和备份工具需要文件形式的 SQLite 数据库")
    path = Path(url.database).expanduser()
    if not path.is_absolute():
        path = (base_dir or Path.cwd()) / path
    return path.resolve()


def _read_only_connection(database_path: Path) -> sqlite3.Connection:
    if not database_path.is_file():
        raise FileNotFoundError(f"SQLite 数据库不存在：{database_path}")
    encoded_path = quote(database_path.as_posix(), safe="/:")
    connection = sqlite3.connect(f"file:{encoded_path}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def _safe_relative_storage_path(raw_path: str) -> str | None:
    if not raw_path or ":" in raw_path or "\\" in raw_path:
        return None
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    return relative.as_posix()


def _storage_files(materials_root: Path) -> set[str]:
    if not materials_root.is_dir():
        return set()
    return {
        path.relative_to(materials_root).as_posix()
        for path in materials_root.rglob("*")
        if path.is_file()
    }


def audit_data(database_path: Path, materials_root: Path) -> AuditReport:
    """Audit active records and storage without creating, changing, or deleting data."""

    resolved_database = database_path.expanduser().resolve()
    resolved_storage = materials_root.expanduser().resolve()
    with _read_only_connection(resolved_database) as connection:
        rows = connection.execute(
            """
            SELECT COALESCE(storage_path, '')
            FROM materials
            WHERE deleted_at IS NULL
            """
        ).fetchall()
        genre_metric_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM genre_metrics WHERE deleted_at IS NULL"
            ).fetchone()[0]
        )

    raw_paths = [str(row[0] or "") for row in rows]
    attachment_paths = [path for path in raw_paths if path]
    referenced_paths = {
        safe_path
        for raw_path in attachment_paths
        if (safe_path := _safe_relative_storage_path(raw_path)) is not None
    }
    actual_files = _storage_files(resolved_storage)
    missing_count = sum(
        1
        for raw_path in attachment_paths
        if (safe_path := _safe_relative_storage_path(raw_path)) is None
        or safe_path not in actual_files
    )
    return AuditReport(
        material_count=len(raw_paths),
        # "Has attachment" means the record carries attachment metadata;
        # missing physical files are reported separately as a subset.
        attachment_material_count=len(attachment_paths),
        legacy_without_attachment_count=sum(1 for path in raw_paths if not path),
        missing_attachment_file_count=missing_count,
        orphan_file_count=len(actual_files - referenced_paths),
        genre_metric_count=genre_metric_count,
    )


def _default_materials_root(settings: object) -> Path:
    material_storage_path = getattr(settings, "material_storage_path", None)
    if material_storage_path is not None:
        return Path(material_storage_path)
    return Path(getattr(settings, "storage_root")) / "materials"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="只读审计素材数据库与文件存储的一致性")
    parser.add_argument("--database-url", help="覆盖环境配置中的 DATABASE_URL")
    parser.add_argument("--materials-root", type=Path, help="覆盖素材文件根目录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出审计结果")
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="存在数据库引用但物理附件缺失时返回非零退出码",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    from app.core.config import get_settings

    args = _build_parser().parse_args(argv)
    settings = get_settings()
    database_path = sqlite_database_path(args.database_url or settings.database_url)
    materials_root = args.materials_root or _default_materials_root(settings)
    try:
        report = audit_data(database_path, materials_root)
    except (FileNotFoundError, sqlite3.DatabaseError, ValueError) as exc:
        print(f"数据审计失败：{exc}")
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"素材总数：{report.material_count}")
        print(f"有附件素材数：{report.attachment_material_count}")
        print(f"无附件旧素材数：{report.legacy_without_attachment_count}")
        print(f"数据库记录存在但文件缺失数量：{report.missing_attachment_file_count}")
        print(f"存储目录存在但数据库无记录的孤立文件数量：{report.orphan_file_count}")
        print(f"定位数据数量：{report.genre_metric_count}")
    if args.fail_on_missing and report.missing_attachment_file_count > 0:
        print("数据审计失败：存在缺失的素材附件")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
