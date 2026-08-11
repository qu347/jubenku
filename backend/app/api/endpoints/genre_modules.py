from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.genre import (
    GenreModuleCreate,
    GenreModuleDetail,
    GenreModuleRead,
    GenreModuleUpdate,
    ModuleSectionCreate,
    ModuleSectionRead,
    ModuleSectionUpdate,
    ReorderPayload,
)
from app.services.genre_service import GenreService

router = APIRouter(tags=["genre-modules"])


@router.get("/genre-modules", response_model=ApiResponse[list[GenreModuleRead]])
def list_genre_modules(
    include_inactive: bool = Query(default=False),
    include_hidden: bool = Query(default=False),
    include_deleted: bool = Query(default=False),
    status_filter: str | None = Query(default=None, alias="status", pattern=r"^(active|inactive|disabled|archived)$"),
    keyword: str | None = Query(default=None, min_length=1, max_length=100),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenreService(session).list_modules(
        include_inactive=include_inactive,
        include_hidden=include_hidden,
        include_deleted=include_deleted,
        module_status=status_filter,
        keyword=keyword,
    )
    return {"success": True, "data": data, "message": "题材模块列表获取成功"}


@router.post(
    "/genre-modules",
    response_model=ApiResponse[GenreModuleRead],
    status_code=status.HTTP_201_CREATED,
)
def create_genre_module(payload: GenreModuleCreate, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).create_module(payload)
    return {"success": True, "data": data, "message": "题材模块创建成功"}


# Fixed paths must be declared before /{module_id} UUID paths.
@router.patch("/genre-modules/batch/reorder", response_model=ApiResponse[list[GenreModuleRead]])
def reorder_genre_modules(payload: ReorderPayload, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).reorder_modules(payload)
    return {"success": True, "data": data, "message": "题材模块排序已保存"}


@router.get("/genre-modules/slug/{slug}", response_model=ApiResponse[GenreModuleDetail])
def get_genre_module_by_slug(
    slug: str,
    include_disabled: bool = Query(default=False),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenreService(session).get_module_by_slug(slug, include_disabled=include_disabled)
    return {"success": True, "data": data, "message": "题材模块获取成功"}


@router.get("/genre-modules/{module_id}", response_model=ApiResponse[GenreModuleRead])
def get_genre_module(module_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).get_module(str(module_id))
    return {"success": True, "data": data, "message": "题材模块获取成功"}


@router.patch("/genre-modules/{module_id}", response_model=ApiResponse[GenreModuleRead])
def update_genre_module(
    module_id: UUID,
    payload: GenreModuleUpdate,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenreService(session).update_module(str(module_id), payload)
    return {"success": True, "data": data, "message": "题材模块更新成功"}


@router.delete("/genre-modules/{module_id}", response_model=ApiResponse[dict[str, str]])
def delete_genre_module(module_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).delete_module(str(module_id))
    return {"success": True, "data": data, "message": "题材模块已软删除"}


@router.post("/genre-modules/{module_id}/duplicate", response_model=ApiResponse[GenreModuleRead])
def duplicate_genre_module(module_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).duplicate_module(str(module_id))
    return {"success": True, "data": data, "message": "题材模块复制成功"}


@router.post("/genre-modules/{module_id}/enable", response_model=ApiResponse[GenreModuleRead])
def enable_genre_module(module_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).set_module_enabled(str(module_id), True)
    return {"success": True, "data": data, "message": "题材模块已启用"}


@router.post("/genre-modules/{module_id}/disable", response_model=ApiResponse[GenreModuleRead])
def disable_genre_module(module_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).set_module_enabled(str(module_id), False)
    return {"success": True, "data": data, "message": "题材模块已停用"}


@router.get(
    "/genre-modules/{module_id}/sections",
    response_model=ApiResponse[list[ModuleSectionRead]],
)
def list_module_sections(
    module_id: UUID,
    include_disabled: bool = Query(default=False),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenreService(session).list_sections(str(module_id), include_disabled=include_disabled)
    return {"success": True, "data": data, "message": "功能板块列表获取成功"}


@router.post(
    "/genre-modules/{module_id}/sections",
    response_model=ApiResponse[ModuleSectionRead],
    status_code=status.HTTP_201_CREATED,
)
def create_module_section(
    module_id: UUID,
    payload: ModuleSectionCreate,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenreService(session).create_section(str(module_id), payload)
    return {"success": True, "data": data, "message": "功能板块创建成功"}


@router.patch("/module-sections/batch/reorder", response_model=ApiResponse[list[ModuleSectionRead]])
def reorder_module_sections(payload: ReorderPayload, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).reorder_sections(payload)
    return {"success": True, "data": data, "message": "功能板块排序已保存"}


@router.get("/module-sections/{section_id}", response_model=ApiResponse[ModuleSectionRead])
def get_module_section(section_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).get_section(str(section_id))
    return {"success": True, "data": data, "message": "功能板块获取成功"}


@router.patch("/module-sections/{section_id}", response_model=ApiResponse[ModuleSectionRead])
def update_module_section(
    section_id: UUID,
    payload: ModuleSectionUpdate,
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    data = GenreService(session).update_section(str(section_id), payload)
    return {"success": True, "data": data, "message": "功能板块更新成功"}


@router.delete("/module-sections/{section_id}", response_model=ApiResponse[dict[str, str]])
def delete_module_section(section_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).delete_section(str(section_id))
    return {"success": True, "data": data, "message": "功能板块已软删除"}


@router.post("/module-sections/{section_id}/enable", response_model=ApiResponse[ModuleSectionRead])
def enable_module_section(section_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).set_section_enabled(str(section_id), True)
    return {"success": True, "data": data, "message": "功能板块已启用"}


@router.post("/module-sections/{section_id}/disable", response_model=ApiResponse[ModuleSectionRead])
def disable_module_section(section_id: UUID, session: Session = Depends(get_db)) -> dict[str, Any]:
    data = GenreService(session).set_section_enabled(str(section_id), False)
    return {"success": True, "data": data, "message": "功能板块已停用"}
