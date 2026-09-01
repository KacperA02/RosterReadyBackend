"""make shift generation idempotent

Revision ID: c6a203fa130b
Revises: f88f4b58d0d6
Create Date: 2026-09-01
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c6a203fa130b"
down_revision: Union[str, None] = "f88f4b58d0d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_shift_templates_team_name", "shift_templates", ["team_id", "name"]
    )
    op.create_unique_constraint(
        "uq_shift_instances_template_start", "shift_instances", ["template_id", "starts_at"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_shift_instances_template_start", "shift_instances", type_="unique")
    op.drop_constraint("uq_shift_templates_team_name", "shift_templates", type_="unique")
