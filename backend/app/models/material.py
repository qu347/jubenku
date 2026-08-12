from typing import Any, TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.genre import GenreModule, ModuleSection
    from app.models.project import Project, ProjectMaterial
    from app.models.tag import MaterialTag, Tag


class Material(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "materials"

    library_type: Mapped[str] = mapped_column(
        String(20), default="material", server_default="material", nullable=False, index=True
    )
    genre_module_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("genre_modules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    section_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("module_sections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    material_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    genre: Mapped[str] = mapped_column(String(50), default="", nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), default="original", nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Sprint 3 keeps the earlier content fields for backward compatibility while
    # adding the metadata required by one-record-per-uploaded-file storage.
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(200), default="", nullable=False, index=True)
    uploaded_by: Mapped[str] = mapped_column(String(100), default="", nullable=False, index=True)
    project_owner: Mapped[str] = mapped_column(String(100), default="", nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), default="", nullable=False, index=True)
    stored_filename: Mapped[str] = mapped_column(String(255), default="", nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    file_extension: Mapped[str] = mapped_column(String(20), default="", nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(150), default="application/octet-stream", nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, index=True)

    project: Mapped["Project | None"] = relationship(back_populates="primary_materials")
    genre_module: Mapped["GenreModule | None"] = relationship(back_populates="materials")
    section: Mapped["ModuleSection | None"] = relationship(back_populates="materials")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="material_tags",
        back_populates="materials",
        lazy="selectin",
        overlaps="material,material_tag_links,tag",
    )
    material_tag_links: Mapped[list["MaterialTag"]] = relationship(
        back_populates="material", cascade="all, delete-orphan", overlaps="tags,materials"
    )
    projects: Mapped[list["Project"]] = relationship(
        secondary="project_materials",
        back_populates="materials",
        overlaps="material,project,project_material_links",
    )
    project_material_links: Mapped[list["ProjectMaterial"]] = relationship(
        back_populates="material", cascade="all, delete-orphan", overlaps="materials,projects"
    )
    versions: Mapped[list["MaterialVersion"]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="MaterialVersion.version_number.desc()",
    )
    outgoing_relations: Mapped[list["MaterialRelation"]] = relationship(
        foreign_keys="MaterialRelation.source_material_id",
        back_populates="source_material",
        cascade="all, delete-orphan",
    )
    incoming_relations: Mapped[list["MaterialRelation"]] = relationship(
        foreign_keys="MaterialRelation.target_material_id",
        back_populates="target_material",
        cascade="all, delete-orphan",
    )


class MaterialRelation(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "material_relations"
    __table_args__ = (
        UniqueConstraint(
            "source_material_id", "target_material_id", "relation_type", name="uq_material_relation"
        ),
    )

    source_material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(50), default="related", nullable=False, index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, nullable=False)

    source_material: Mapped[Material] = relationship(
        foreign_keys=[source_material_id], back_populates="outgoing_relations"
    )
    target_material: Mapped[Material] = relationship(
        foreign_keys=[target_material_id], back_populates="incoming_relations"
    )


class MaterialVersion(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "material_versions"
    __table_args__ = (
        UniqueConstraint("material_id", "version_number", name="uq_material_version"),
    )

    material_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    change_note: Mapped[str] = mapped_column(String(200), default="保存内容", nullable=False)

    material: Mapped[Material] = relationship(back_populates="versions")


from app.models.tag import MaterialTag  # noqa: E402

material_tags = MaterialTag.__table__
