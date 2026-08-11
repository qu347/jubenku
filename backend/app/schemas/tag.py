from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    material_count: int = 0
    model_config = ConfigDict(from_attributes=True)
