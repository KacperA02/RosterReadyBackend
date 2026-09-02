"""preserve removed assignment events

Revision ID: d8842fb79d26
Revises: c6a203fa130b
Create Date: 2026-09-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8842fb79d26"
down_revision: Union[str, None] = "c6a203fa130b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "assignment_events", "assignment_id", existing_type=sa.BigInteger(), nullable=True
    )
    op.drop_constraint(
        "assignment_events_assignment_id_fkey", "assignment_events", type_="foreignkey"
    )
    op.create_foreign_key(
        "assignment_events_assignment_id_fkey",
        "assignment_events",
        "assignments",
        ["assignment_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.execute("DELETE FROM assignment_events WHERE assignment_id IS NULL")
    op.drop_constraint(
        "assignment_events_assignment_id_fkey", "assignment_events", type_="foreignkey"
    )
    op.create_foreign_key(
        "assignment_events_assignment_id_fkey",
        "assignment_events",
        "assignments",
        ["assignment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "assignment_events", "assignment_id", existing_type=sa.BigInteger(), nullable=False
    )
