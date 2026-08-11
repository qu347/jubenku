"""Complete Sprint 1 model invariants and associations.

Revision ID: 20260810_0003
Revises: 20260810_0002
"""

from datetime import datetime, timezone
import uuid

from alembic import op
import sqlalchemy as sa

revision = "20260810_0003"
down_revision = "20260810_0002"
branch_labels = None
depends_on = None


def _timestamp_columns(table_name: str, *, add_created_index: bool = True) -> None:
    if add_created_index:
        op.create_index(f"ix_{table_name}_created_at", table_name, ["created_at"])
    op.create_index(f"ix_{table_name}_updated_at", table_name, ["updated_at"])
    op.create_index(f"ix_{table_name}_deleted_at", table_name, ["deleted_at"])


def upgrade() -> None:
    now_default = sa.text("CURRENT_TIMESTAMP")

    for table_name, column_name in (
        ("genre_modules", "name"),
        ("genre_modules", "slug"),
        ("projects", "name"),
        ("tags", "name"),
    ):
        index_name = f"ix_{table_name}_{column_name}"
        op.drop_index(index_name, table_name=table_name)
        op.create_index(index_name, table_name, [column_name], unique=True)

    with op.batch_alter_table("projects") as batch:
        batch.add_column(sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    _timestamp_columns("projects")

    with op.batch_alter_table("tags") as batch:
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now_default))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    _timestamp_columns("tags")

    with op.batch_alter_table("module_sections") as batch:
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_module_sections_section_name", ["section_name"])
        batch.create_index("ix_module_sections_sort_order", ["sort_order"])
    _timestamp_columns("module_sections")

    with op.batch_alter_table("genre_metrics") as batch:
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    _timestamp_columns("genre_metrics")
    op.create_index("ix_genre_modules_created_at", "genre_modules", ["created_at"])
    op.create_index("ix_genre_modules_updated_at", "genre_modules", ["updated_at"])

    with op.batch_alter_table("material_versions") as batch:
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now_default))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_unique_constraint("uq_material_version", ["material_id", "version_number"])
        batch.create_index("ix_material_versions_version_number", ["version_number"])
    _timestamp_columns("material_versions")

    with op.batch_alter_table("material_relations") as batch:
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now_default))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"))
        batch.create_unique_constraint(
            "uq_material_relation",
            ["source_material_id", "target_material_id", "relation_type"],
        )
        batch.create_index("ix_material_relations_relation_type", ["relation_type"])
    _timestamp_columns("material_relations")

    connection = op.get_bind()
    legacy_rows = list(connection.execute(sa.text("SELECT material_id, tag_id FROM material_tags")))
    op.rename_table("material_tags", "material_tags_legacy")
    op.create_table(
        "material_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.String(36), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("material_id", "tag_id", name="uq_material_tag"),
    )
    material_tags = sa.table(
        "material_tags",
        sa.column("id", sa.String),
        sa.column("material_id", sa.String),
        sa.column("tag_id", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("deleted_at", sa.DateTime(timezone=True)),
    )
    timestamp = datetime.now(timezone.utc)
    if legacy_rows:
        op.bulk_insert(material_tags, [
            {
                "id": str(uuid.uuid4()),
                "material_id": row.material_id,
                "tag_id": row.tag_id,
                "created_at": timestamp,
                "updated_at": timestamp,
                "deleted_at": None,
            }
            for row in legacy_rows
        ])
    op.drop_table("material_tags_legacy")
    for name, columns in (
        ("ix_material_tags_material_id", ["material_id"]),
        ("ix_material_tags_tag_id", ["tag_id"]),
        ("ix_material_tags_created_at", ["created_at"]),
        ("ix_material_tags_updated_at", ["updated_at"]),
        ("ix_material_tags_deleted_at", ["deleted_at"]),
    ):
        op.create_index(name, "material_tags", columns)

    op.create_table(
        "project_materials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="reference"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "material_id", name="uq_project_material"),
    )
    for name, columns in (
        ("ix_project_materials_project_id", ["project_id"]),
        ("ix_project_materials_material_id", ["material_id"]),
        ("ix_project_materials_role", ["role"]),
        ("ix_project_materials_created_at", ["created_at"]),
        ("ix_project_materials_updated_at", ["updated_at"]),
        ("ix_project_materials_deleted_at", ["deleted_at"]),
    ):
        op.create_index(name, "project_materials", columns)


def downgrade() -> None:
    op.drop_table("project_materials")

    connection = op.get_bind()
    active_links = list(connection.execute(sa.text(
        "SELECT material_id, tag_id FROM material_tags WHERE deleted_at IS NULL"
    )))
    op.rename_table("material_tags", "material_tags_sprint1")
    op.create_table(
        "material_tags",
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(36), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )
    legacy = sa.table("material_tags", sa.column("material_id", sa.String), sa.column("tag_id", sa.String))
    if active_links:
        op.bulk_insert(legacy, [{"material_id": row.material_id, "tag_id": row.tag_id} for row in active_links])
    op.drop_table("material_tags_sprint1")

    with op.batch_alter_table("material_relations") as batch:
        batch.drop_index("ix_material_relations_updated_at")
        batch.drop_index("ix_material_relations_deleted_at")
        batch.drop_index("ix_material_relations_created_at")
        batch.drop_index("ix_material_relations_relation_type")
        batch.drop_constraint("uq_material_relation", type_="unique")
        batch.drop_column("metadata")
        batch.drop_column("deleted_at")
        batch.drop_column("updated_at")
    with op.batch_alter_table("material_versions") as batch:
        batch.drop_index("ix_material_versions_updated_at")
        batch.drop_index("ix_material_versions_deleted_at")
        batch.drop_index("ix_material_versions_created_at")
        batch.drop_index("ix_material_versions_version_number")
        batch.drop_constraint("uq_material_version", type_="unique")
        batch.drop_column("deleted_at")
        batch.drop_column("updated_at")
    op.drop_index("ix_genre_modules_updated_at", table_name="genre_modules")
    op.drop_index("ix_genre_modules_created_at", table_name="genre_modules")
    with op.batch_alter_table("genre_metrics") as batch:
        batch.drop_index("ix_genre_metrics_updated_at")
        batch.drop_index("ix_genre_metrics_deleted_at")
        batch.drop_index("ix_genre_metrics_created_at")
        batch.drop_column("deleted_at")
    with op.batch_alter_table("module_sections") as batch:
        batch.drop_index("ix_module_sections_updated_at")
        batch.drop_index("ix_module_sections_deleted_at")
        batch.drop_index("ix_module_sections_created_at")
        batch.drop_index("ix_module_sections_sort_order")
        batch.drop_index("ix_module_sections_section_name")
        batch.drop_column("deleted_at")
    with op.batch_alter_table("tags") as batch:
        batch.drop_index("ix_tags_updated_at")
        batch.drop_index("ix_tags_deleted_at")
        batch.drop_index("ix_tags_created_at")
        batch.drop_column("deleted_at")
        batch.drop_column("updated_at")
    with op.batch_alter_table("projects") as batch:
        batch.drop_index("ix_projects_updated_at")
        batch.drop_index("ix_projects_deleted_at")
        batch.drop_index("ix_projects_created_at")
        batch.drop_column("deleted_at")
        batch.drop_column("metadata")

    for table_name, column_name in (
        ("genre_modules", "name"),
        ("genre_modules", "slug"),
        ("projects", "name"),
        ("tags", "name"),
    ):
        index_name = f"ix_{table_name}_{column_name}"
        op.drop_index(index_name, table_name=table_name)
        op.create_index(index_name, table_name, [column_name], unique=False)
