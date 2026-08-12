"""Add material upload platform positioning metadata.

Revision ID: 20260812_0008
Revises: 20260812_0007
"""

from alembic import op
import sqlalchemy as sa


revision = "20260812_0008"
down_revision = "20260812_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.add_column(sa.Column("upload_platform", sa.String(60), nullable=True))
        batch.add_column(sa.Column("platform_heat", sa.Float(), nullable=True))
        batch.create_index("ix_materials_upload_platform", ["upload_platform"])
        batch.create_index("ix_materials_platform_heat", ["platform_heat"])
        batch.create_check_constraint(
            "ck_materials_platform_heat_range",
            "platform_heat IS NULL OR (platform_heat >= 0 AND platform_heat <= 100)",
        )


def downgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.drop_constraint("ck_materials_platform_heat_range", type_="check")
        batch.drop_index("ix_materials_platform_heat")
        batch.drop_index("ix_materials_upload_platform")
        batch.drop_column("platform_heat")
        batch.drop_column("upload_platform")
