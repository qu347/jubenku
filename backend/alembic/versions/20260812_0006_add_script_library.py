"""Add material/script library discriminator.

Revision ID: 20260812_0006
Revises: 20260811_0005
"""

from alembic import op
import sqlalchemy as sa


revision = "20260812_0006"
down_revision = "20260811_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.add_column(
            sa.Column(
                "library_type",
                sa.String(20),
                nullable=False,
                server_default="material",
            )
        )
        batch.create_index("ix_materials_library_type", ["library_type"])


def downgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.drop_index("ix_materials_library_type")
        batch.drop_column("library_type")
