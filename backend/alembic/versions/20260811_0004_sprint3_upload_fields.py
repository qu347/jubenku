"""Add Sprint 3 upload metadata.

Revision ID: 20260811_0004
Revises: 20260810_0003
"""

from alembic import op
import sqlalchemy as sa

revision = "20260811_0004"
down_revision = "20260810_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.add_column(sa.Column("description", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("tags_json", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("source", sa.String(200), nullable=False, server_default=""))
        batch.add_column(sa.Column("original_filename", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("stored_filename", sa.String(255), nullable=False, server_default=""))
        batch.add_column(sa.Column("storage_path", sa.String(500), nullable=False, server_default=""))
        batch.add_column(sa.Column("file_extension", sa.String(20), nullable=False, server_default=""))
        batch.add_column(
            sa.Column(
                "mime_type",
                sa.String(150),
                nullable=False,
                server_default="application/octet-stream",
            )
        )
        batch.add_column(sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"))
        batch.create_index("ix_materials_source", ["source"])
        batch.create_index("ix_materials_original_filename", ["original_filename"])
        batch.create_index("ix_materials_stored_filename", ["stored_filename"])
        batch.create_index("ix_materials_file_extension", ["file_extension"])
        batch.create_index("ix_materials_file_size", ["file_size"])

def downgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.drop_index("ix_materials_file_size")
        batch.drop_index("ix_materials_file_extension")
        batch.drop_index("ix_materials_stored_filename")
        batch.drop_index("ix_materials_original_filename")
        batch.drop_index("ix_materials_source")
        batch.drop_column("file_size")
        batch.drop_column("mime_type")
        batch.drop_column("file_extension")
        batch.drop_column("storage_path")
        batch.drop_column("stored_filename")
        batch.drop_column("original_filename")
        batch.drop_column("source")
        batch.drop_column("tags_json")
        batch.drop_column("description")
