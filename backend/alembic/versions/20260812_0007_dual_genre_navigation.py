"""Add independent material and script genre navigation settings.

Revision ID: 20260812_0007
Revises: 20260812_0006
"""

from alembic import op
import sqlalchemy as sa


revision = "20260812_0007"
down_revision = "20260812_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("genre_modules") as batch:
        batch.add_column(
            sa.Column("material_visible", sa.Boolean(), nullable=False, server_default="1")
        )
        batch.add_column(
            sa.Column("script_visible", sa.Boolean(), nullable=False, server_default="1")
        )
        batch.add_column(
            sa.Column("material_sort_order", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(
            sa.Column("script_sort_order", sa.Integer(), nullable=False, server_default="0")
        )
        batch.create_index("ix_genre_modules_material_visible", ["material_visible"])
        batch.create_index("ix_genre_modules_script_visible", ["script_visible"])
        batch.create_index("ix_genre_modules_material_sort_order", ["material_sort_order"])
        batch.create_index("ix_genre_modules_script_sort_order", ["script_sort_order"])

    op.execute(
        "UPDATE genre_modules SET material_visible = visible, script_visible = visible, "
        "material_sort_order = sort_order, script_sort_order = sort_order"
    )


def downgrade() -> None:
    with op.batch_alter_table("genre_modules") as batch:
        batch.drop_index("ix_genre_modules_script_sort_order")
        batch.drop_index("ix_genre_modules_material_sort_order")
        batch.drop_index("ix_genre_modules_script_visible")
        batch.drop_index("ix_genre_modules_material_visible")
        batch.drop_column("script_sort_order")
        batch.drop_column("material_sort_order")
        batch.drop_column("script_visible")
        batch.drop_column("material_visible")
