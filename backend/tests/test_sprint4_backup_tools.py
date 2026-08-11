from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from app.tools.audit_data import audit_data, main as audit_main
from app.tools.backup import cleanup_expired_backups, create_backup
from app.tools.verify_backup import sha256_file, verify_backup


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _create_audit_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE materials (
                id TEXT PRIMARY KEY,
                storage_path TEXT,
                deleted_at TEXT
            );
            CREATE TABLE genre_metrics (
                id TEXT PRIMARY KEY,
                deleted_at TEXT
            );
            CREATE TABLE alembic_version (
                version_num TEXT PRIMARY KEY
            );
            INSERT INTO alembic_version VALUES ('20260811_0004');
            INSERT INTO materials VALUES ('present', '2026/08/present.txt', NULL);
            INSERT INTO materials VALUES ('missing', '2026/08/missing.txt', NULL);
            INSERT INTO materials VALUES ('legacy', '', NULL);
            INSERT INTO materials VALUES ('deleted', '2026/08/deleted.txt', '2026-08-11');
            INSERT INTO genre_metrics VALUES ('active-metric', NULL);
            INSERT INTO genre_metrics VALUES ('deleted-metric', '2026-08-11');
            """
        )


def _create_source(
    tmp_path: Path,
    *,
    include_missing_record: bool = False,
) -> tuple[Path, Path, Path]:
    database_path = tmp_path / "source.db"
    materials_root = tmp_path / "source-storage" / "materials"
    backup_root = tmp_path / "backups"
    materials_root.joinpath("2026", "08").mkdir(parents=True)
    materials_root.joinpath("2026", "08", "present.txt").write_text(
        "中文素材内容",
        encoding="utf-8",
    )
    _create_audit_database(database_path)
    if not include_missing_record:
        with sqlite3.connect(database_path) as connection:
            connection.execute("DELETE FROM materials WHERE id = 'missing'")
    return database_path, materials_root, backup_root


def test_audit_is_read_only_and_reports_missing_and_orphan_files(tmp_path: Path) -> None:
    database_path, materials_root, _ = _create_source(tmp_path, include_missing_record=True)
    orphan = materials_root / "orphan.txt"
    orphan.write_text("orphan", encoding="utf-8")
    database_hash_before = _file_hash(database_path)
    present_hash_before = _file_hash(materials_root / "2026" / "08" / "present.txt")

    report = audit_data(database_path, materials_root)

    assert report.to_dict() == {
        "material_count": 3,
        "attachment_material_count": 2,
        "legacy_without_attachment_count": 1,
        "missing_attachment_file_count": 1,
        "orphan_file_count": 1,
        "genre_metric_count": 1,
    }
    assert _file_hash(database_path) == database_hash_before
    assert _file_hash(materials_root / "2026" / "08" / "present.txt") == present_hash_before
    assert orphan.is_file()


def test_audit_treats_unsafe_database_path_as_missing_without_leaving_storage(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "audit.db"
    materials_root = tmp_path / "materials"
    materials_root.mkdir()
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE materials (id TEXT, storage_path TEXT, deleted_at TEXT);
            CREATE TABLE genre_metrics (id TEXT, deleted_at TEXT);
            INSERT INTO materials VALUES ('unsafe', '../outside.txt', NULL);
            """
        )
    outside = tmp_path / "outside.txt"
    outside.write_text("must remain", encoding="utf-8")

    report = audit_data(database_path, materials_root)

    assert report.missing_attachment_file_count == 1
    assert outside.read_text(encoding="utf-8") == "must remain"


def test_audit_cli_can_block_startup_when_attachment_is_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path, materials_root, _ = _create_source(
        tmp_path,
        include_missing_record=True,
    )

    exit_code = audit_main(
        [
            "--database-url",
            f"sqlite:///{database_path.as_posix()}",
            "--materials-root",
            str(materials_root),
            "--fail-on-missing",
        ]
    )

    assert exit_code == 2
    assert "存在缺失的素材附件" in capsys.readouterr().out


def test_backup_copies_database_storage_and_generates_verified_manifest(tmp_path: Path) -> None:
    database_path, materials_root, backup_root = _create_source(tmp_path)
    source_database_hash = sha256_file(database_path)
    source_file = materials_root / "2026" / "08" / "present.txt"
    source_file_hash = sha256_file(source_file)

    result = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
        retention_days=30,
        now=datetime(2026, 8, 11, 1, 2, 3, tzinfo=timezone.utc),
    )

    backup_database = result.backup_directory / "database" / "script_materials.db"
    backup_file = result.backup_directory / "storage" / "materials" / "2026" / "08" / "present.txt"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert backup_database.is_file()
    assert backup_file.is_file()
    assert (result.backup_directory / "backup.log").is_file()
    assert manifest["status"] == "complete"
    assert manifest["verification"]["status"] == "passed"
    assert manifest["database"]["sha256"] == sha256_file(backup_database)
    assert manifest["storage"]["file_count"] == 1
    assert manifest["storage"]["total_size_bytes"] == backup_file.stat().st_size
    assert manifest["storage"]["files"][0]["path"] == "2026/08/present.txt"
    assert verify_backup(result.backup_directory).valid is True
    # Backing up must never mutate either production source.
    assert sha256_file(database_path) == source_database_hash
    assert sha256_file(source_file) == source_file_hash


def test_sqlite_backup_api_includes_committed_wal_content(tmp_path: Path) -> None:
    database_path = tmp_path / "wal-source.db"
    materials_root = tmp_path / "materials"
    materials_root.mkdir()
    backup_root = tmp_path / "backups"
    writer = sqlite3.connect(database_path)
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
        writer.executescript(
            """
            CREATE TABLE committed_data (value TEXT NOT NULL);
            CREATE TABLE materials (id TEXT, storage_path TEXT, deleted_at TEXT);
            CREATE TABLE alembic_version (version_num TEXT);
            INSERT INTO alembic_version VALUES ('20260811_0004');
            INSERT INTO committed_data VALUES ('未检查点的中文数据');
            """
        )
        writer.commit()

        result = create_backup(
            database_path=database_path,
            materials_root=materials_root,
            backup_root=backup_root,
        )
    finally:
        writer.close()

    backup_database = result.backup_directory / "database" / "script_materials.db"
    with sqlite3.connect(backup_database) as restored:
        assert restored.execute("SELECT value FROM committed_data").fetchone()[0] == "未检查点的中文数据"


def test_verify_backup_rejects_corrupted_database_even_if_manifest_hash_is_changed(
    tmp_path: Path,
) -> None:
    database_path, materials_root, backup_root = _create_source(tmp_path)
    result = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
    )
    backup_database = result.backup_directory / "database" / "script_materials.db"
    backup_database.write_bytes(b"not-a-sqlite-database")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    manifest["database"]["size_bytes"] = backup_database.stat().st_size
    manifest["database"]["sha256"] = sha256_file(backup_database)
    result.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    verification = verify_backup(result.backup_directory)

    assert verification.valid is False
    assert any("损坏" in error or "完整性" in error for error in verification.errors)


def test_verify_backup_rejects_missing_storage_file(tmp_path: Path) -> None:
    database_path, materials_root, backup_root = _create_source(tmp_path)
    result = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
    )
    backed_up_file = (
        result.backup_directory / "storage" / "materials" / "2026" / "08" / "present.txt"
    )
    backed_up_file.unlink()

    verification = verify_backup(result.backup_directory)

    assert verification.valid is False
    assert any("数量" in error or "清单" in error for error in verification.errors)


def test_backup_fails_when_database_references_a_missing_storage_file(tmp_path: Path) -> None:
    database_path, materials_root, backup_root = _create_source(
        tmp_path,
        include_missing_record=True,
    )

    try:
        create_backup(
            database_path=database_path,
            materials_root=materials_root,
            backup_root=backup_root,
        )
    except RuntimeError as exc:
        assert "数据库引用的素材文件缺失" in str(exc)
    else:
        raise AssertionError("数据库引用缺失文件时不能发布成功备份")

    failed_manifest = json.loads(
        next(backup_root.iterdir()).joinpath("manifest.json").read_text(encoding="utf-8")
    )
    assert failed_manifest["status"] == "failed"


def test_backup_failure_does_not_publish_or_mark_a_backup_successful(tmp_path: Path) -> None:
    database_path = tmp_path / "broken.db"
    database_path.write_bytes(b"broken")
    materials_root = tmp_path / "materials"
    materials_root.mkdir()
    backup_root = tmp_path / "backups"

    try:
        create_backup(
            database_path=database_path,
            materials_root=materials_root,
            backup_root=backup_root,
        )
    except sqlite3.DatabaseError:
        pass
    else:
        raise AssertionError("损坏数据库必须导致备份失败")

    failed_directories = list(backup_root.iterdir())
    assert len(failed_directories) == 1
    manifest = json.loads((failed_directories[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["verification"]["status"] == "failed"
    assert verify_backup(failed_directories[0]).valid is False


def test_backup_root_cannot_be_nested_inside_production_storage(tmp_path: Path) -> None:
    database_path, materials_root, _ = _create_source(tmp_path)
    source_file = materials_root / "2026" / "08" / "present.txt"

    try:
        create_backup(
            database_path=database_path,
            materials_root=materials_root,
            backup_root=materials_root / "backups",
        )
    except ValueError as exc:
        assert "不能位于素材目录内部" in str(exc)
    else:
        raise AssertionError("备份目录位于正式素材目录内时必须拒绝执行")

    assert source_file.read_text(encoding="utf-8") == "中文素材内容"
    assert not (materials_root / "backups").exists()


def test_retention_removes_only_expired_completed_backups_after_new_verification(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    database_path, materials_root, backup_root = _create_source(tmp_path)
    current = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
    expired = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
        retention_days=365,
        now=current - timedelta(days=60),
    )
    recent = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
        retention_days=365,
        now=current - timedelta(days=10),
    )

    removed: list[Path] = []
    monkeypatch.setattr("app.tools.backup.shutil.rmtree", lambda path: removed.append(Path(path)))
    newest = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
        retention_days=30,
        now=current,
    )

    assert removed == [expired.backup_directory]
    assert recent.backup_directory.is_dir()
    assert newest.backup_directory.is_dir()
    assert newest.deleted_expired_backups == (expired.backup_directory,)


def test_retention_does_nothing_when_the_new_backup_is_not_valid(tmp_path: Path) -> None:
    database_path, materials_root, backup_root = _create_source(tmp_path)
    current = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)
    expired = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
        retention_days=365,
        now=current - timedelta(days=60),
    )
    invalid_new = create_backup(
        database_path=database_path,
        materials_root=materials_root,
        backup_root=backup_root,
        retention_days=365,
        now=current,
    )
    (invalid_new.backup_directory / "storage" / "materials" / "2026" / "08" / "present.txt").unlink()

    deleted = cleanup_expired_backups(
        backup_root,
        retention_days=30,
        verified_backup=invalid_new.backup_directory,
        now=current,
    )

    assert deleted == []
    assert expired.backup_directory.is_dir()
