import json
from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.database.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.material import (
    MaterialDeleteResult,
    MaterialPage,
    MaterialRead,
    MaterialUpdate,
    MaterialUploadResult,
)
from app.services.material_service import MaterialService

router = APIRouter(prefix="/materials", tags=["materials"])


def _parse_values(values: list[str]) -> list[str]:
    parsed: list[str] = []
    for value in values:
        value = value.strip()
        if not value:
            continue
        if value.startswith("["):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError as exc:
                raise AppException(
                    "标签必须是 JSON 数组或逗号分隔文本",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="invalid_tags",
                ) from exc
            if not isinstance(decoded, list) or not all(isinstance(item, str) for item in decoded):
                raise AppException(
                    "标签必须是字符串数组",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="invalid_tags",
                )
            parsed.extend(decoded)
        else:
            parsed.extend(value.split(","))
    normalized: list[str] = []
    seen: set[str] = set()
    for item in parsed:
        tag = item.strip()
        if not tag:
            continue
        if len(tag) > 50:
            raise AppException(
                "单个标签不能超过 50 个字符",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="invalid_tags",
            )
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(tag)
    if len(normalized) > 30:
        raise AppException(
            "标签数量不能超过 30 个",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="invalid_tags",
        )
    return normalized


@router.post("/upload", response_model=ApiResponse[MaterialUploadResult])
async def upload_materials(
    files: Annotated[list[UploadFile], File(min_length=1)],
    genre_module_id: Annotated[UUID | None, Form()] = None,
    material_type: Annotated[str, Form(min_length=1, max_length=30)] = "参考资料",
    tags: Annotated[list[str], Form()] = [],
    source: Annotated[str, Form(max_length=200)] = "",
    description: Annotated[str, Form(max_length=20_000)] = "",
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = await MaterialService(session).upload(
        files=files,
        genre_module_id=str(genre_module_id) if genre_module_id else None,
        material_type=material_type,
        tags=_parse_values(tags),
        source=source,
        description=description,
    )
    return {"success": True, "data": data, "message": "素材文件处理完成", "error": None}


@router.get("", response_model=ApiResponse[MaterialPage])
def list_materials(
    keyword: str | None = Query(default=None, max_length=100),
    genre_module_id: UUID | None = None,
    material_type: str | None = Query(default=None, max_length=30),
    file_extension: str | None = Query(default=None, max_length=20),
    tags: list[str] = Query(default=[]),
    source: str | None = Query(default=None, max_length=200),
    uploaded_from: date | None = None,
    uploaded_to: date | None = None,
    sort: str = Query(
        default="created_desc",
        pattern=r"^(created_desc|created_asc|updated_desc|updated_asc|title_asc|title_desc|file_size_desc|file_size_asc)$",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = MaterialService(session).list(
        keyword=keyword,
        genre_module_id=str(genre_module_id) if genre_module_id else None,
        material_type=material_type,
        file_extension=file_extension,
        tags=_parse_values(tags),
        source=source,
        uploaded_from=uploaded_from,
        uploaded_to=uploaded_to,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return {"success": True, "data": data, "message": "素材列表获取成功", "error": None}


@router.get("/{material_id}/download")
def download_material(material_id: UUID, session: Session = Depends(get_db)) -> FileResponse:
    material, path = MaterialService(session).download(str(material_id))
    return FileResponse(
        path,
        media_type=material.mime_type,
        filename=material.original_filename,
    )


@router.get("/{material_id}", response_model=ApiResponse[MaterialRead])
def get_material(material_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    return {
        "success": True,
        "data": MaterialService(session).get(str(material_id)),
        "message": "素材详情获取成功",
        "error": None,
    }


@router.patch("/{material_id}", response_model=ApiResponse[MaterialRead])
def update_material(
    material_id: UUID,
    payload: MaterialUpdate,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    return {
        "success": True,
        "data": MaterialService(session).update(str(material_id), payload),
        "message": "素材元数据更新成功",
        "error": None,
    }


@router.delete("/{material_id}", response_model=ApiResponse[MaterialDeleteResult])
def delete_material(material_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    return {
        "success": True,
        "data": MaterialService(session).delete(str(material_id)),
        "message": "素材及物理文件已删除",
        "error": None,
    }

