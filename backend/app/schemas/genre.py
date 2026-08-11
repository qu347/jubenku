from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


GenreStatus = Literal["active", "inactive", "disabled", "archived"]


class GenreModuleBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    icon: str = Field(default="Collection", max_length=50)
    description: str = Field(default="", max_length=5000)
    theme_color: str = Field(default="#f59e0b", pattern=r"^#[0-9a-fA-F]{6}$")
    sort_order: int = Field(default=0, ge=0)
    status: GenreStatus = "active"
    visible: bool = True
    profile_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "slug")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()


class GenreModuleCreate(GenreModuleBase):
    create_default_sections: bool = True


class GenreModuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    icon: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=5000)
    theme_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    sort_order: int | None = Field(default=None, ge=0)
    status: GenreStatus | None = None
    visible: bool | None = None
    profile_json: dict[str, Any] | None = None

    @field_validator("name", "slug")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class GenreModuleRead(GenreModuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    section_count: int = 0
    material_count: int = 0

    model_config = ConfigDict(from_attributes=True)


FIELD_TYPES = {
    "text", "textarea", "markdown", "number", "date", "select",
    "multiselect", "tags", "image", "url", "relation",
}


class FieldDefinition(BaseModel):
    key: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", max_length=80)
    label: str = Field(min_length=1, max_length=100)
    type: str
    required: bool = False
    sort_order: int = Field(default=0, ge=0)
    options: list[str] = Field(default_factory=list)
    placeholder: str = Field(default="", max_length=200)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in FIELD_TYPES:
            raise ValueError(f"不支持的字段类型：{value}")
        return value

    @model_validator(mode="after")
    def validate_options(self) -> "FieldDefinition":
        if self.type in {"select", "multiselect"} and not self.options:
            raise ValueError("select 和 multiselect 字段必须提供非空 options")
        return self


class ModuleSectionBase(BaseModel):
    section_key: str = Field(pattern=r"^[a-z0-9_]+$", max_length=80)
    section_name: str = Field(min_length=2, max_length=50)
    icon: str = Field(default="Document", max_length=50)
    sort_order: int = Field(default=0, ge=0)
    enabled: bool = True
    field_schema: list[FieldDefinition] = Field(default_factory=list)
    filter_schema: dict[str, Any] = Field(default_factory=dict)
    card_schema: dict[str, Any] = Field(default_factory=dict)


class ModuleSectionCreate(ModuleSectionBase):
    pass


class ModuleSectionUpdate(BaseModel):
    section_key: str | None = Field(default=None, pattern=r"^[a-z0-9_]+$", max_length=80)
    section_name: str | None = Field(default=None, min_length=2, max_length=50)
    icon: str | None = Field(default=None, max_length=50)
    sort_order: int | None = Field(default=None, ge=0)
    enabled: bool | None = None
    field_schema: list[FieldDefinition] | None = None
    filter_schema: dict[str, Any] | None = None
    card_schema: dict[str, Any] | None = None


class ModuleSectionRead(ModuleSectionBase):
    id: UUID
    genre_module_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    material_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class GenreModuleDetail(GenreModuleRead):
    sections: list[ModuleSectionRead] = Field(default_factory=list)


class ReorderItem(BaseModel):
    id: UUID
    sort_order: int = Field(ge=0)


class ReorderPayload(BaseModel):
    items: list[ReorderItem] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "ReorderPayload":
        if len({item.id for item in self.items}) != len(self.items):
            raise ValueError("排序列表中不能出现重复 ID")
        return self


# Backward-compatible names used by earlier Sprint 1 code.
SectionCreate = ModuleSectionCreate
SectionUpdate = ModuleSectionUpdate
SectionRead = ModuleSectionRead
