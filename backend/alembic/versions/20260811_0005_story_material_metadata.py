"""Add story material ownership metadata.

Revision ID: 20260811_0005
Revises: 20260811_0004
"""

from alembic import op
import sqlalchemy as sa


revision = "20260811_0005"
down_revision = "20260811_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.add_column(sa.Column("uploaded_by", sa.String(100), nullable=False, server_default=""))
        batch.add_column(sa.Column("project_owner", sa.String(100), nullable=False, server_default=""))
        batch.create_index("ix_materials_uploaded_by", ["uploaded_by"])
        batch.create_index("ix_materials_project_owner", ["project_owner"])


def downgrade() -> None:
    with op.batch_alter_table("materials") as batch:
        batch.drop_index("ix_materials_project_owner")
        batch.drop_index("ix_materials_uploaded_by")
        batch.drop_column("project_owner")
        batch.drop_column("uploaded_by")
