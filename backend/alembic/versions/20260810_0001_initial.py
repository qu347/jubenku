"""Initial material library schema.

Revision ID: 20260810_0001
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "20260810_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_projects_name", "projects", ["name"])
    op.create_index("ix_projects_status", "projects", ["status"])

    op.create_table(
        "tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_tags_name", "tags", ["name"])

    op.create_table(
        "materials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("material_type", sa.String(30), nullable=False),
        sa.Column("genre", sa.String(50), nullable=False, server_default=""),
        sa.Column("summary", sa.String(300), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cover_url", sa.String(500), nullable=True),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="original"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    for name, columns in (
        ("ix_materials_title", ["title"]),
        ("ix_materials_material_type", ["material_type"]),
        ("ix_materials_genre", ["genre"]),
        ("ix_materials_status", ["status"]),
        ("ix_materials_project_id", ["project_id"]),
        ("ix_materials_source_type", ["source_type"]),
        ("ix_materials_favorite", ["favorite"]),
        ("ix_materials_created_at", ["created_at"]),
        ("ix_materials_updated_at", ["updated_at"]),
        ("ix_materials_deleted_at", ["deleted_at"]),
    ):
        op.create_index(name, "materials", columns)

    op.create_table(
        "material_tags",
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(36), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "material_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("change_note", sa.String(200), nullable=False, server_default="保存内容"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_material_versions_material_id", "material_versions", ["material_id"])


def downgrade() -> None:
    op.drop_table("material_versions")
    op.drop_table("material_tags")
    op.drop_table("materials")
    op.drop_table("tags")
    op.drop_table("projects")
