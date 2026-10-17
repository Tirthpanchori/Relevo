"""At most one running attempt for a job, even if a coordination path regresses.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_attempts_running_job",
        "attempts",
        ["job_id"],
        unique=True,
        postgresql_where=sa.text("state = 'running'"),
    )


def downgrade() -> None:
    op.drop_index("uq_attempts_running_job", table_name="attempts")
