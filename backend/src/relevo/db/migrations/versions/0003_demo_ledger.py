"""Separate demonstration business-operation and effect tables.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA relevo_demo")
    op.create_table(
        "operations",
        sa.Column("business_key", sa.String(200), primary_key=True),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        schema="relevo_demo",
    )
    op.create_table(
        "effects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("business_key", sa.String(200), nullable=False),
        sa.Column("operation_key", sa.String(200), nullable=True),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["operation_key"], ["relevo_demo.operations.business_key"]),
        sa.UniqueConstraint("operation_key"),
        sa.CheckConstraint("units >= 1 AND units <= 1000000", name="ck_demo_effect_units"),
        sa.CheckConstraint(
            "operation_key IS NULL OR operation_key=business_key", name="ck_demo_effect_key"
        ),
        schema="relevo_demo",
    )


def downgrade() -> None:
    op.drop_table("effects", schema="relevo_demo")
    op.drop_table("operations", schema="relevo_demo")
    op.execute("DROP SCHEMA relevo_demo")
