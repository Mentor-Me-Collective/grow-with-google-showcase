"""one active run per programme, and a started_at

Revision ID: 51ca8036b7de
Revises: 2d879bfa7a79
Create Date: 2026-08-15 19:14:56.828150

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "51ca8036b7de"
down_revision: str | None = "2d879bfa7a79"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ACTIVE_RUN_INDEX = "uq_run_one_active_per_program"


def upgrade() -> None:
    op.add_column(
        "run", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Any programme already holding more than one active run would make the
    # index below impossible to create, and there is no honest way to keep both:
    # a run whose process is gone is not running, whatever the column says. The
    # newest survives because it is the one somebody is most likely watching.
    op.execute(
        sa.text(
            """
            UPDATE run SET state = 'discarded', progress = 1.0
            WHERE state IN ('queued', 'running')
              AND id NOT IN (
                SELECT DISTINCT ON (program_id) id FROM run
                WHERE state IN ('queued', 'running')
                ORDER BY program_id, created_at DESC
              )
            """
        )
    )

    # The invariant is "at most one active run per programme", and this is what
    # enforces it. The check in the router is a courtesy that produces a good
    # error message; it cannot be the guarantee, because two requests can both
    # pass it before either inserts. A partial index refuses the second insert
    # outright, and needs no lock on a row that does not exist yet.
    op.create_index(
        ACTIVE_RUN_INDEX,
        "run",
        ["program_id"],
        unique=True,
        postgresql_where=sa.text("state IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_index(ACTIVE_RUN_INDEX, table_name="run")
    op.drop_column("run", "started_at")
