from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_tags(value: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        tag = item.strip()
        if not tag:
            continue
        if len(tag) > 50:
            raise ValueError("单个标签不能超过 50 个字符")
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(tag)
    if len(normalized) > 30:
        raise ValueError("标签数量不能超过 30 个")
    return normalized


class GenreModuleBrief(BaseModel):
    id: str
    name: str
    slug: str
    theme_color: str

    model_config = ConfigDict(from_attributes=True)


class MaterialUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    genre_module_id: str | None = None
    material_type: str | None = Field(default=None, min_length=1, max_length=30)
    tags: list[str] | None = None
    source: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=20_000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("title", "material_type")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

    @field_validator("source", "description")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | None) -> list[str] | None:
        return _normalize_tags(value) if value is not None else None


class MaterialRead(BaseModel):
    id: str
    genre_module_id: str | None
    genre_module: GenreModuleBrief | None = None
    title: str
    material_type: str
    description: str
    legacy_summary: str
    legacy_content: str
    tags: list[str]
    source: str
    original_filename: str
    stored_filename: str
    storage_path: str
    file_extension: str
    mime_type: str
    file_size: int
    has_attachment: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class MaterialPage(BaseModel):
    items: list[MaterialRead]
    total: int
    page: int
    page_size: int
    pages: int


class UploadFileResult(BaseModel):
    filename: str
    success: bool
    material_id: str | None = None
    error: str | None = None


class MaterialUploadResult(BaseModel):
    success_count: int
    failure_count: int
    results: list[UploadFileResult]
    materials: list[MaterialRead]


class MaterialDeleteResult(BaseModel):
    id: str
    file_deleted: bool
