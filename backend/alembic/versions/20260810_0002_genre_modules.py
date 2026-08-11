"""genre modules and configurable sections

Revision ID: 20260810_0002
Revises: 20260810_0001
"""
from alembic import op
import sqlalchemy as sa

revision = "20260810_0002"
down_revision = "20260810_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "genre_modules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("icon", sa.String(50), nullable=False, server_default="Collection"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("theme_color", sa.String(20), nullable=False, server_default="#f59e0b"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name"), sa.UniqueConstraint("slug"),
    )
    for name, columns in (
        ("ix_genre_modules_name", ["name"]), ("ix_genre_modules_slug", ["slug"]),
        ("ix_genre_modules_sort_order", ["sort_order"]), ("ix_genre_modules_status", ["status"]),
        ("ix_genre_modules_visible", ["visible"]), ("ix_genre_modules_deleted_at", ["deleted_at"]),
    ):
        op.create_index(name, "genre_modules", columns)

    op.create_table(
        "module_sections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("genre_module_id", sa.String(36), sa.ForeignKey("genre_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_key", sa.String(80), nullable=False),
        sa.Column("section_name", sa.String(100), nullable=False),
        sa.Column("icon", sa.String(50), nullable=False, server_default="Document"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("field_schema", sa.JSON(), nullable=False),
        sa.Column("filter_schema", sa.JSON(), nullable=False),
        sa.Column("card_schema", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("genre_module_id", "section_key", name="uq_module_section_key"),
    )
    op.create_index("ix_module_sections_genre_module_id", "module_sections", ["genre_module_id"])
    op.create_index("ix_module_sections_section_key", "module_sections", ["section_key"])
    op.create_index("ix_module_sections_enabled", "module_sections", ["enabled"])

    op.create_table(
        "genre_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("genre_module_id", sa.String(36), sa.ForeignKey("genre_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(60), nullable=False),
        sa.Column("channel", sa.String(60), nullable=False),
        sa.Column("period", sa.String(60), nullable=False),
        sa.Column("average_age", sa.Float(), nullable=False),
        sa.Column("age_group", sa.String(30), nullable=False),
        sa.Column("education_level", sa.String(30), nullable=False),
        sa.Column("audience_share", sa.Float(), nullable=False),
        sa.Column("heat_index", sa.Float(), nullable=False),
        sa.Column("trend", sa.String(30), nullable=False),
        sa.Column("is_core", sa.Boolean(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("data_source", sa.String(200), nullable=False),
        sa.Column("remark", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name, columns in (
        ("ix_genre_metrics_genre_module_id", ["genre_module_id"]), ("ix_genre_metrics_platform", ["platform"]),
        ("ix_genre_metrics_channel", ["channel"]), ("ix_genre_metrics_period", ["period"]),
        ("ix_genre_metrics_age_group", ["age_group"]), ("ix_genre_metrics_education_level", ["education_level"]),
        ("ix_genre_metrics_trend", ["trend"]), ("ix_genre_metrics_is_core", ["is_core"]),
    ):
        op.create_index(name, "genre_metrics", columns)

    with op.batch_alter_table("materials") as batch:
        batch.add_column(sa.Column("genre_module_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("section_id", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_material_genre_module", "genre_modules", ["genre_module_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_material_section", "module_sections", ["section_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_materials_genre_module_id", ["genre_module_id"])
        batch.create_index("ix_materials_section_id", ["section_id"])

    op.create_table(
        "material_relations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False, server_default="related"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_material_relations_source_material_id", "material_relations", ["source_material_id"])
    op.create_index("ix_material_relations_target_material_id", "material_relations", ["target_material_id"])


def downgrade() -> None:
    op.drop_table("material_relations")
    with op.batch_alter_table("materials") as batch:
        batch.drop_index("ix_materials_section_id")
        batch.drop_index("ix_materials_genre_module_id")
        batch.drop_constraint("fk_material_section", type_="foreignkey")
        batch.drop_constraint("fk_material_genre_module", type_="foreignkey")
        batch.drop_column("section_id")
        batch.drop_column("genre_module_id")
    op.drop_table("genre_metrics")
    op.drop_table("module_sections")
    op.drop_table("genre_modules")
