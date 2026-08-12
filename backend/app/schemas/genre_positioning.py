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


class GenrePositioningTimelinePoint(BaseModel):
    genre_module_id: str
    genre_name: str
    theme_color: str
    period: str
    average_heat: float
    material_count: int


class GenrePositioningTimeline(BaseModel):
    upload_platform: str
    periods: list[str]
    points: list[GenrePositioningTimelinePoint]
    total_materials: int
