from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.material import Material


class ProjectMaterial(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "project_materials"
    __table_args__ = (
        UniqueConstraint("project_id", "material_id", name="uq_project_material"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), default="reference", nullable=False, index=True)

    project: Mapped["Project"] = relationship(back_populates="project_material_links", overlaps="materials,projects")
    material: Mapped["Material"] = relationship(back_populates="project_material_links", overlaps="materials,projects")


class Project(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    primary_materials: Mapped[list["Material"]] = relationship(back_populates="project")
    materials: Mapped[list["Material"]] = relationship(
        secondary="project_materials",
        back_populates="projects",
        overlaps="material,project,project_material_links",
    )
    project_material_links: Mapped[list[ProjectMaterial]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        overlaps="materials,projects",
    )
