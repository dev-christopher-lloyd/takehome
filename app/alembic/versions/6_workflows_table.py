from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

revision = "6_workflows_table"      
down_revision = "5_campaigns_products_table"   
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
      "workflows",
      sa.Column("id", sa.Integer, primary_key=True),

      sa.Column(
          "campaign_id",
          sa.Integer,
          sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
          nullable=False,
      ),

      sa.Column("status", sa.Integer, nullable=False),

      sa.Column(
          "started_at",
          sa.DateTime(timezone=True),
          server_default=func.now(),
          nullable=False,
      ),
      sa.Column(
          "finished_at",
          sa.DateTime(timezone=True),
          nullable=True,
      ),

      sa.Column("error_message", sa.Text, nullable=True),
  )

  op.create_index(
      "ix_workflows_campaign_id",
      "workflows",
      ["campaign_id"],
  )
  op.create_index(
      "ix_workflows_status",
      "workflows",
      ["status"],
  )


def downgrade():
  op.drop_index("ix_workflows_status", table_name="workflows")
  op.drop_index("ix_workflows_campaign_id", table_name="workflows")
  op.drop_table("workflows")
