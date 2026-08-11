import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

AgeGroup = Literal["youth", "middle", "senior"]
EducationLevel = Literal["low", "medium", "high"]
Trend = Literal["rising", "stable", "falling"]

PERIOD_PATTERN = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2]|Q[1-4])$")


def validate_period(value: str) -> str:
    normalized = value.strip().upper()
    if not PERIOD_PATTERN.fullmatch(normalized):
        raise ValueError("数据周期格式应为 YYYY-MM 或 YYYY-Q1")
    return normalized


class GenreModuleBrief(BaseModel):
    id: str
    name: str
    slug: str
    theme_color: str

    model_config = ConfigDict(from_attributes=True)


class GenreMetricCreate(BaseModel):
    genre_module_id: UUID
    platform: str = Field(min_length=1, max_length=60)
    channel: str = Field(min_length=1, max_length=60)
    period: str
    average_age: float = Field(gt=0, le=100)
    age_group: AgeGroup
    education_level: EducationLevel
    audience_share: float = Field(ge=0, le=100)
    heat_index: float = Field(ge=0, le=100)
    trend: Trend = "stable"
    is_core: bool = False
    sample_size: int = Field(default=0, ge=0)
    data_source: str = Field(default="", max_length=200)
    remark: str = Field(default="", max_length=20_000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("platform", "channel")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

    @field_validator("data_source", "remark")
    @classmethod
    def strip_optional_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("period")
    @classmethod
    def period_format(cls, value: str) -> str:
        return validate_period(value)


class GenreMetricUpdate(BaseModel):
    genre_module_id: UUID | None = None
    platform: str | None = Field(default=None, min_length=1, max_length=60)
    channel: str | None = Field(default=None, min_length=1, max_length=60)
    period: str | None = None
    average_age: float | None = Field(default=None, gt=0, le=100)
    age_group: AgeGroup | None = None
    education_level: EducationLevel | None = None
    audience_share: float | None = Field(default=None, ge=0, le=100)
    heat_index: float | None = Field(default=None, ge=0, le=100)
    trend: Trend | None = None
    is_core: bool | None = None
    sample_size: int | None = Field(default=None, ge=0)
    data_source: str | None = Field(default=None, max_length=200)
    remark: str | None = Field(default=None, max_length=20_000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("platform", "channel")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

    @field_validator("data_source", "remark")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("period")
    @classmethod
    def period_format(cls, value: str | None) -> str | None:
        return validate_period(value) if value is not None else None


class GenreMetricRead(BaseModel):
    id: str
    genre_module_id: str
    genre_module: GenreModuleBrief
    platform: str
    channel: str
    period: str
    average_age: float
    age_group: AgeGroup
    education_level: EducationLevel
    audience_share: float
    heat_index: float
    trend: Trend
    is_core: bool
    sample_size: int
    data_source: str
    remark: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class GenreMetricPage(BaseModel):
    items: list[GenreMetricRead]
    total: int
    page: int
    page_size: int
    pages: int


class GenreMetricDeleteResult(BaseModel):
    id: str


class ImportErrorItem(BaseModel):
    row: int
    field: str
    reason: str


class GenreMetricImportResult(BaseModel):
    success_count: int
    failure_count: int
    errors: list[ImportErrorItem]
