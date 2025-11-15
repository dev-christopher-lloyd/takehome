from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

revision = "9_checks_table"           # set your actual revision id
down_revision = "8_workflows_table"  # adjust to your migration chain
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "checks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "workflow_run_id",
            sa.Integer,
            sa.ForeignKey("workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            sa.Integer,
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_type", sa.Integer, nullable=False),
        sa.Column("result", sa.Integer, nullable=False),
        sa.Column("details_json", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_checks_workflow_run_id",
        "checks",
        ["workflow_run_id"],
    )
    op.create_index(
        "ix_checks_asset_id",
        "checks",
        ["asset_id"],
    )
    op.create_index(
        "ix_checks_check_type",
        "checks",
        ["check_type"],
    )
    op.create_index(
        "ix_checks_result",
        "checks",
        ["result"],
    )


def downgrade():
    op.drop_index("ix_checks_result", table_name="checks")
    op.drop_index("ix_checks_check_type", table_name="checks")
    op.drop_index("ix_checks_asset_id", table_name="checks")
    op.drop_index("ix_checks_workflow_run_id", table_name="checks")
    op.drop_table("checks")
