from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class UploadPlatform(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "upload_platforms"

    name: Mapped[str] = mapped_column(String(60), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=1000, nullable=False, index=True)
