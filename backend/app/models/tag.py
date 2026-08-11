from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.material import Material


class MaterialTag(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "material_tags"
    __table_args__ = (
        UniqueConstraint("material_id", "tag_id", name="uq_material_tag"),
    )

    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True
    )

    material: Mapped["Material"] = relationship(back_populates="material_tag_links", overlaps="tags")
    tag: Mapped["Tag"] = relationship(back_populates="material_tag_links", overlaps="materials,tags")


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    materials: Mapped[list["Material"]] = relationship(
        secondary="material_tags",
        back_populates="tags",
        lazy="selectin",
        overlaps="material,material_tag_links,tag",
    )
    material_tag_links: Mapped[list[MaterialTag]] = relationship(
        back_populates="tag", cascade="all, delete-orphan", overlaps="materials,tags"
    )
