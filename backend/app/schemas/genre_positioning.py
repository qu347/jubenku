from datetime import datetime

from pydantic import BaseModel


class GenrePositioningItem(BaseModel):
    genre_module_id: str
    genre_name: str
    theme_color: str
    upload_platform: str
    average_heat: float
    material_count: int
    latest_updated_at: datetime


class GenrePositioningList(BaseModel):
    items: list[GenrePositioningItem]
    total: int
