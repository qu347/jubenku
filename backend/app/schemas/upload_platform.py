import unicodedata

from pydantic import BaseModel, Field, field_validator


class UploadPlatformCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return unicodedata.normalize("NFKC", value).strip()


class UploadPlatformRead(BaseModel):
    id: str
    name: str
    is_system: bool
