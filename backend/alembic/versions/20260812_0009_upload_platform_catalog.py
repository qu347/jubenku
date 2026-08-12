"""Add persistent upload platform catalog.

Revision ID: 20260812_0009
Revises: 20260812_0008
"""

from datetime import datetime, timezone
import unicodedata
import uuid

from alembic import op
import sqlalchemy as sa


revision = "20260812_0009"
down_revision = "20260812_0008"
branch_labels = None
depends_on = None


DEFAULT_UPLOAD_PLATFORMS: tuple[str, ...] = (
    "番茄小说",
    "七猫",
    "起点中文网",
    "晋江文学城",
    "纵横中文网",
    "抖音",
    "快手",
    "小红书",
    "微信公众号",
    "知乎",
)
PLATFORM_NAMESPACE = uuid.UUID("d4264d31-c35d-41f3-a583-20e48eed13e7")


def _normalize(value: str) -> tuple[str, str]:
    display = unicodedata.normalize("NFKC", value).strip()
    return display, display.casefold()


def _row(name: str, *, is_system: bool, sort_order: int, now: datetime) -> dict[str, object]:
    display, normalized = _normalize(name)
    return {
        "id": str(uuid.uuid5(PLATFORM_NAMESPACE, normalized)),
        "name": display,
        "normalized_name": normalized,
        "is_system": is_system,
        "sort_order": sort_order,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }


def upgrade() -> None:
    op.create_table(
        "upload_platforms",
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("normalized_name", sa.String(length=120), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_upload_platforms_created_at", "upload_platforms", ["created_at"])
    op.create_index("ix_upload_platforms_deleted_at", "upload_platforms", ["deleted_at"])
    op.create_index("ix_upload_platforms_is_system", "upload_platforms", ["is_system"])
    op.create_index(
        "ix_upload_platforms_normalized_name",
        "upload_platforms",
        ["normalized_name"],
        unique=True,
    )
    op.create_index("ix_upload_platforms_sort_order", "upload_platforms", ["sort_order"])
    op.create_index("ix_upload_platforms_updated_at", "upload_platforms", ["updated_at"])

    bind = op.get_bind()
    table = sa.table(
        "upload_platforms",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("normalized_name", sa.String),
        sa.column("is_system", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("deleted_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    rows = [
        _row(name, is_system=True, sort_order=index, now=now)
        for index, name in enumerate(DEFAULT_UPLOAD_PLATFORMS)
    ]
    known = {str(row["normalized_name"]) for row in rows}
    historical_names = bind.execute(
        sa.text(
            "SELECT DISTINCT upload_platform FROM materials "
            "WHERE upload_platform IS NOT NULL AND trim(upload_platform) <> ''"
        )
    ).scalars()
    for name in historical_names:
        display, normalized = _normalize(name)
        if not display or normalized in known:
            continue
        known.add(normalized)
        rows.append(_row(display, is_system=False, sort_order=1000, now=now))
    op.bulk_insert(table, rows)


def downgrade() -> None:
    op.drop_table("upload_platforms")
