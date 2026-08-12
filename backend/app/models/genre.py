from typing import Any, TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.material import Material


class GenreModule(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "genre_modules"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    icon: Mapped[str] = mapped_column(String(50), default="Collection", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    theme_color: Mapped[str] = mapped_column(String(20), default="#f59e0b", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    material_visible: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False, index=True
    )
    script_visible: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False, index=True
    )
    material_sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False, index=True
    )
    script_sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False, index=True
    )
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    sections: Mapped[list["ModuleSection"]] = relationship(
        back_populates="genre_module",
        cascade="all, delete-orphan",
        order_by="ModuleSection.sort_order",
    )
    metrics: Mapped[list["GenreMetric"]] = relationship(
        back_populates="genre_module", cascade="all, delete-orphan"
    )
    materials: Mapped[list["Material"]] = relationship(back_populates="genre_module")


class ModuleSection(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "module_sections"
    __table_args__ = (
        UniqueConstraint("genre_module_id", "section_key", name="uq_module_section_key"),
    )

    genre_module_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("genre_modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    section_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    icon: Mapped[str] = mapped_column(String(50), default="Document", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    field_schema: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    filter_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    card_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    genre_module: Mapped[GenreModule] = relationship(back_populates="sections")
    materials: Mapped[list["Material"]] = relationship(back_populates="section")


class GenreMetric(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "genre_metrics"

    genre_module_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("genre_modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(60), default="综合平台", nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(60), default="全频道", nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(60), default="2026-08", nullable=False, index=True)
    average_age: Mapped[float] = mapped_column(Float, nullable=False)
    age_group: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    education_level: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    audience_share: Mapped[float] = mapped_column(Float, nullable=False)
    heat_index: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    trend: Mapped[str] = mapped_column(String(30), default="stable", nullable=False, index=True)
    is_core: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_source: Mapped[str] = mapped_column(String(200), default="原创模拟调研", nullable=False)
    remark: Mapped[str] = mapped_column(Text, default="", nullable=False)

    genre_module: Mapped[GenreModule] = relationship(back_populates="metrics")
