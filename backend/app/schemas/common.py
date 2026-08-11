from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "操作成功"
    error: Any | None = None


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int
