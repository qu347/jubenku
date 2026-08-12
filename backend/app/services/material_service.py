import codecs
import logging
import math
import mimetypes
import os
import zipfile
from xml.etree import ElementTree
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from fastapi import UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.models import GenreModule, Material
from app.repositories.material_repository import MaterialRepository
from app.schemas.material import MaterialUpdate


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".txt",
    ".md",
    ".jpg",
    ".jpeg",
    ".png",
}

ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"},
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
}

logger = logging.getLogger("app.materials")


class UploadRejected(Exception):
    pass


def validate_platform_metadata(
    library_type: str,
    upload_platform: str | None,
    platform_heat: float | None,
    *,
    require_for_material: bool,
) -> tuple[str | None, float | None]:
    platform = upload_platform.strip() if upload_platform else None
    if platform_heat is not None and not 0 <= platform_heat <= 100:
        raise AppException(
            "平台热度必须在 0 到 100 之间",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_platform_heat",
        )
    if library_type == "material" and require_for_material and (not platform or platform_heat is None):
        raise AppException(
            "请选择或输入上传平台，并填写平台热度",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="material_platform_required",
        )
    if bool(platform) != (platform_heat is not None):
        raise AppException(
            "上传平台和平台热度必须同时填写或同时清空",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="incomplete_platform_metadata",
        )
    return platform, platform_heat


def material_to_dict(
    material: Material,
    *,
    content_text: str = "",
    content_truncated: bool = False,
) -> dict[str, Any]:
    genre_module = material.genre_module
    legacy_tags = [
        link.tag.name
        for link in material.material_tag_links
        if link.deleted_at is None and link.tag is not None and link.tag.deleted_at is None
    ]
    return {
        "id": material.id,
        "library_type": material.library_type,
        "genre_module_id": material.genre_module_id,
        "genre_module": (
            {
                "id": genre_module.id,
                "name": genre_module.name,
                "slug": genre_module.slug,
                "theme_color": genre_module.theme_color,
            }
            if genre_module
            else None
        ),
        "title": material.title,
        "material_type": material.material_type,
        "description": material.description,
        "legacy_summary": material.summary if not material.storage_path else "",
        "legacy_content": material.content if not material.storage_path else "",
        "tags": list(material.tags_json or []) or legacy_tags,
        "source": material.source,
        "uploaded_by": material.uploaded_by,
        "project_owner": material.project_owner,
        "upload_platform": material.upload_platform,
        "platform_heat": material.platform_heat,
        "content_text": content_text,
        "content_truncated": content_truncated,
        "original_filename": material.original_filename,
        "stored_filename": material.stored_filename,
        "storage_path": material.storage_path,
        "file_extension": material.file_extension,
        "mime_type": material.mime_type,
        "file_size": material.file_size,
        "has_attachment": bool(material.storage_path),
        "created_at": material.created_at,
        "updated_at": material.updated_at,
        "deleted_at": material.deleted_at,
    }


class MaterialService:
    def __init__(self, session: Session, storage_root: Path | None = None) -> None:
        self.session = session
        self.repository = MaterialRepository(session)
        self.storage_root = (storage_root or settings.material_storage_path).resolve()

    def _require_module(self, module_id: str | None) -> GenreModule | None:
        module = self.repository.get_module(module_id) if module_id else None
        if module_id and not module:
            raise AppException(
                "题材模块不存在",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="genre_module_not_found",
                details={"field": "genre_module_id"},
            )
        return module

    def _get(self, material_id: str) -> Material:
        material = self.repository.get(material_id)
        if not material:
            raise AppException(
                "素材不存在",
                status_code=status.HTTP_404_NOT_FOUND,
                code="material_not_found",
            )
        return material

    @staticmethod
    def _safe_original_filename(filename: str | None) -> str:
        # Normalize both slash styles before selecting the basename. The
        # original name is metadata only and is never joined to a server path.
        normalized = (filename or "").replace("\\", "/")
        name = PurePosixPath(normalized).name.strip()
        if not name or name in {".", ".."}:
            raise UploadRejected("文件名无效")
        return name[:255]

    @staticmethod
    def _validate_type(filename: str, content_type: str | None) -> tuple[str, str]:
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise UploadRejected(f"不支持的文件扩展名：{extension or '无扩展名'}")
        provided_mime = (content_type or "").split(";", 1)[0].strip().lower()
        allowed_mimes = ALLOWED_MIME_TYPES[extension]
        if provided_mime and provided_mime != "application/octet-stream" and provided_mime not in allowed_mimes:
            raise UploadRejected("文件 MIME 类型与扩展名不匹配")
        guessed_mime = mimetypes.guess_type(filename)[0]
        verified_mime = "" if provided_mime == "application/octet-stream" else provided_mime
        return extension, verified_mime or guessed_mime or "application/octet-stream"

    @staticmethod
    def _validate_signature(extension: str, header: bytes, path: Path, *, complete_sample: bool) -> None:
        normalized_header = header.lstrip(b"\xef\xbb\xbf\r\n\t ")
        if extension == ".pdf" and not normalized_header.startswith(b"%PDF-"):
            raise UploadRejected("PDF 文件签名无效")
        if extension == ".png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise UploadRejected("PNG 文件签名无效")
        if extension in {".jpg", ".jpeg"} and not header.startswith(b"\xff\xd8\xff"):
            raise UploadRejected("JPEG 文件签名无效")
        if extension in {".docx", ".xlsx"}:
            try:
                with zipfile.ZipFile(path) as archive:
                    names = set(archive.namelist())
            except (OSError, zipfile.BadZipFile) as exc:
                raise UploadRejected("Office 文件不是有效的 ZIP 文档") from exc
            required = (
                {"[Content_Types].xml", "word/document.xml"}
                if extension == ".docx"
                else {"[Content_Types].xml", "xl/workbook.xml"}
            )
            if not required.issubset(names):
                raise UploadRejected("Office 文件结构与扩展名不匹配")
        if extension in {".txt", ".md", ".csv"}:
            if b"\x00" in header:
                raise UploadRejected("文本文件包含二进制内容")
            try:
                decoder = codecs.getincrementaldecoder("utf-8-sig")("strict")
                decoder.decode(header, final=complete_sample)
            except UnicodeDecodeError as exc:
                raise UploadRejected("文本文件必须使用 UTF-8 编码") from exc

    def _resolve_upload_target(self, target: Path) -> Path:
        """Resolve every write target and reject junction/symlink escapes."""

        try:
            storage_root = self.storage_root.resolve()
            resolved = target.resolve()
            normalized_storage_root = Path(str(storage_root).removeprefix("\\\\?\\"))
            normalized_target = Path(str(resolved).removeprefix("\\\\?\\"))
            normalized_target.relative_to(normalized_storage_root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise UploadRejected("素材存储目录越界，已拒绝写入") from exc
        return resolved

    async def _store_file(self, upload: UploadFile) -> tuple[dict[str, Any], Path]:
        original_filename = self._safe_original_filename(upload.filename)
        extension, mime_type = self._validate_type(original_filename, upload.content_type)
        now = datetime.now(timezone.utc)
        relative_directory = PurePosixPath(f"{now:%Y}/{now:%m}")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        destination_directory = self._resolve_upload_target(
            self.storage_root.joinpath(*relative_directory.parts)
        )
        destination_directory.mkdir(parents=True, exist_ok=True)
        stored_filename = f"{uuid4()}{extension}"
        relative_path = relative_directory / stored_filename
        final_path = self._resolve_upload_target(destination_directory / stored_filename)
        partial_path = self._resolve_upload_target(
            destination_directory / f".{stored_filename}.part"
        )
        file_size = 0
        header = bytearray()
        text_decoder = (
            codecs.getincrementaldecoder("utf-8-sig")("strict")
            if extension in {".txt", ".md", ".csv"}
            else None
        )
        try:
            with partial_path.open("xb") as destination:
                while chunk := await upload.read(1024 * 1024):
                    file_size += len(chunk)
                    if file_size > settings.max_upload_bytes:
                        raise UploadRejected(f"文件超过 {settings.max_upload_mb}MB 大小限制")
                    if len(header) < 8192:
                        header.extend(chunk[: 8192 - len(header)])
                    if text_decoder:
                        if b"\x00" in chunk:
                            raise UploadRejected("文本文件包含二进制内容")
                        try:
                            text_decoder.decode(chunk, final=False)
                        except UnicodeDecodeError as exc:
                            raise UploadRejected("文本文件必须使用 UTF-8 编码") from exc
                    destination.write(chunk)
            if text_decoder:
                try:
                    text_decoder.decode(b"", final=True)
                except UnicodeDecodeError as exc:
                    raise UploadRejected("文本文件必须使用 UTF-8 编码") from exc
            self._validate_signature(
                extension,
                bytes(header),
                partial_path,
                complete_sample=file_size <= len(header),
            )
            os.replace(partial_path, final_path)
        except Exception:
            partial_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise
        return (
            {
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "storage_path": relative_path.as_posix(),
                "file_extension": extension,
                "mime_type": mime_type,
                "file_size": file_size,
            },
            final_path,
        )

    async def upload(
        self,
        *,
        files: list[UploadFile],
        genre_module_id: str | None,
        material_type: str,
        tags: list[str],
        source: str,
        description: str,
        title: str = "",
        uploaded_by: str = "",
        project_owner: str = "",
        library_type: str = "material",
        upload_platform: str | None = None,
        platform_heat: float | None = None,
    ) -> dict[str, Any]:
        upload_platform, platform_heat = validate_platform_metadata(
            library_type,
            upload_platform,
            platform_heat,
            require_for_material=True,
        )
        genre_module = self._require_module(genre_module_id)
        materials: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        for upload in files:
            display_filename = (upload.filename or "未命名文件").replace("\\", "/").rsplit("/", 1)[-1]
            final_path: Path | None = None
            try:
                display_filename = self._safe_original_filename(upload.filename)
                file_values, final_path = await self._store_file(upload)
                derived_title = Path(file_values["original_filename"]).stem[:100] or "未命名素材"
                display_title = title.strip()[:100] if title.strip() and len(files) == 1 else derived_title
                material = self.repository.create(
                    {
                        "library_type": library_type,
                        "genre_module_id": genre_module_id,
                        "genre_module": genre_module,
                        "title": display_title,
                        "material_type": material_type.strip(),
                        "description": description.strip(),
                        "tags_json": tags,
                        "source": source.strip(),
                        "uploaded_by": uploaded_by.strip(),
                        "project_owner": project_owner.strip(),
                        "upload_platform": upload_platform,
                        "platform_heat": platform_heat,
                        **file_values,
                    }
                )
                self.session.commit()
                logger.info(
                    "material_upload_success material_id=%s extension=%s size=%s",
                    material.id,
                    file_values["file_extension"],
                    file_values["file_size"],
                )
                materials.append(material_to_dict(material))
                results.append(
                    {
                        "filename": display_filename,
                        "success": True,
                        "material_id": material.id,
                        "error": None,
                    }
                )
            except UploadRejected as exc:
                self.session.rollback()
                if final_path:
                    final_path.unlink(missing_ok=True)
                logger.warning(
                    "material_upload_rejected failure_type=%s",
                    type(exc).__name__,
                )
                results.append(
                    {"filename": display_filename, "success": False, "material_id": None, "error": str(exc)}
                )
            except (OSError, SQLAlchemyError) as exc:
                self.session.rollback()
                if final_path:
                    final_path.unlink(missing_ok=True)
                logger.error(
                    "material_upload_failed failure_type=%s",
                    type(exc).__name__,
                )
                results.append(
                    {
                        "filename": display_filename,
                        "success": False,
                        "material_id": None,
                        "error": "文件保存失败，请检查存储目录后重试",
                    }
                )
        return {
            "success_count": len(materials),
            "failure_count": len(results) - len(materials),
            "results": results,
            "materials": materials,
        }

    def list(
        self,
        *,
        library_type: str,
        keyword: str | None,
        genre_module_id: str | None,
        upload_platform: str | None,
        material_type: str | None,
        file_extension: str | None,
        tags: list[str],
        source: str | None,
        uploaded_from: date | None,
        uploaded_to: date | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        if uploaded_from and uploaded_to and uploaded_from > uploaded_to:
            raise AppException(
                "上传开始日期不能晚于结束日期",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="invalid_date_range",
            )
        items, total = self.repository.list(
            library_type=library_type,
            keyword=keyword,
            genre_module_id=genre_module_id,
            upload_platform=upload_platform,
            material_type=material_type,
            file_extension=file_extension,
            tags=tags,
            source=source,
            uploaded_from=uploaded_from,
            uploaded_to=uploaded_to,
            sort=sort,
            page=page,
            page_size=page_size,
        )
        return {
            "items": [material_to_dict(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": math.ceil(total / page_size) if total else 0,
        }

    def _content_preview(self, material: Material, limit: int = 500_000) -> tuple[str, bool]:
        if not material.storage_path:
            return "", False
        path = self._resolve_storage_path(material.storage_path)
        if not path or not path.is_file():
            return "", False
        try:
            if material.file_extension in {".txt", ".md", ".csv"}:
                raw = path.read_bytes()
                text = raw.decode("utf-8-sig")
            elif material.file_extension == ".docx":
                with zipfile.ZipFile(path) as archive:
                    root = ElementTree.fromstring(archive.read("word/document.xml"))
                paragraphs: list[str] = []
                namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                for paragraph in root.iter(f"{namespace}p"):
                    line = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
                    if line:
                        paragraphs.append(line)
                text = "\n".join(paragraphs)
            else:
                return "", False
        except (OSError, UnicodeDecodeError, KeyError, zipfile.BadZipFile, ElementTree.ParseError):
            return "", False
        return text[:limit], len(text) > limit

    def get(self, material_id: str) -> dict[str, Any]:
        material = self._get(material_id)
        content_text, content_truncated = self._content_preview(material)
        return material_to_dict(
            material,
            content_text=content_text,
            content_truncated=content_truncated,
        )

    def update(self, material_id: str, payload: MaterialUpdate) -> dict[str, Any]:
        material = self._get(material_id)
        changes = payload.model_dump(exclude_unset=True)
        upload_platform, platform_heat = validate_platform_metadata(
            material.library_type,
            changes.get("upload_platform", material.upload_platform),
            changes.get("platform_heat", material.platform_heat),
            require_for_material=False,
        )
        if "upload_platform" in changes:
            changes["upload_platform"] = upload_platform
        if "platform_heat" in changes:
            changes["platform_heat"] = platform_heat
        if "genre_module_id" in changes:
            material.genre_module = self._require_module(changes["genre_module_id"])
        if "tags" in changes:
            # Once the legacy record is explicitly edited, retire its old
            # relation rows so an intentionally empty JSON list stays empty
            # on subsequent reads. Tag records themselves remain available.
            retired_at = datetime.now(timezone.utc)
            for link in material.material_tag_links:
                if link.deleted_at is None:
                    link.deleted_at = retired_at
            changes["tags_json"] = changes.pop("tags")
        for field, value in changes.items():
            setattr(material, field, value)
        try:
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise AppException(
                "素材元数据保存失败",
                status_code=status.HTTP_409_CONFLICT,
                code="material_update_failed",
            ) from exc
        return material_to_dict(self._get(material_id))

    def _resolve_storage_path(self, storage_path: str) -> Path | None:
        if not storage_path:
            return None
        if ":" in storage_path or "\\" in storage_path:
            raise AppException("素材存储路径无效", status_code=500, code="unsafe_storage_path")
        relative = PurePosixPath(storage_path)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise AppException("素材存储路径无效", status_code=500, code="unsafe_storage_path")
        target = self.storage_root.joinpath(*relative.parts).resolve()
        try:
            target.relative_to(self.storage_root)
        except ValueError as exc:
            raise AppException("素材存储路径无效", status_code=500, code="unsafe_storage_path") from exc
        return target

    def download(self, material_id: str) -> tuple[Material, Path]:
        material = self._get(material_id)
        path = self._resolve_storage_path(material.storage_path)
        if not path or not path.is_file():
            raise AppException(
                "素材文件不存在",
                status_code=status.HTTP_404_NOT_FOUND,
                code="material_file_not_found",
            )
        return material, path

    def delete(self, material_id: str) -> dict[str, Any]:
        material = self._get(material_id)
        path = self._resolve_storage_path(material.storage_path)
        tombstone: Path | None = None
        backup_content: bytes | None = None
        file_existed = bool(path and path.is_file())
        stage = "prepare"
        try:
            if file_existed and path:
                tombstone = path.with_name(f".{path.name}.{uuid4()}.deleting")
                os.replace(path, tombstone)
                backup_content = tombstone.read_bytes()
            self.repository.delete(material)
            self.session.flush()
            stage = "file_cleanup"
            if tombstone:
                tombstone.unlink()
            stage = "database_commit"
            self.session.commit()
        except Exception as exc:
            logger.error(
                "material_delete_failed material_id=%s stage=%s failure_type=%s",
                material_id,
                stage,
                type(exc).__name__,
            )
            self.session.rollback()
            compensation_error: Exception | None = None
            restoring_path: Path | None = None
            try:
                if path and tombstone and tombstone.exists():
                    os.replace(tombstone, path)
                elif path and backup_content is not None and not path.exists():
                    restoring_path = path.with_name(f".{path.name}.{uuid4()}.restoring")
                    restoring_path.write_bytes(backup_content)
                    os.replace(restoring_path, path)
            except Exception as restore_exc:
                compensation_error = restore_exc
            finally:
                if restoring_path and restoring_path.exists():
                    try:
                        restoring_path.unlink()
                    except OSError:
                        pass
            if compensation_error:
                raise AppException(
                    "素材删除失败，且文件恢复失败，请人工检查存储目录",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    code="material_delete_compensation_failed",
                ) from compensation_error
            if isinstance(exc, AppException):
                raise
            if stage == "file_cleanup":
                raise AppException(
                    "物理文件清理失败，素材记录和原文件已恢复",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    code="material_file_cleanup_failed",
                ) from exc
            raise AppException(
                "素材删除失败，原有数据已恢复",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="material_delete_failed",
            ) from exc
        logger.info(
            "material_delete_success material_id=%s file_deleted=%s",
            material_id,
            file_existed,
        )
        return {"id": material_id, "file_deleted": file_existed}
