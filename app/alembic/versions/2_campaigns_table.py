from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

revision = "2_campaigns_table"
down_revision = "1_brands_table"
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
      "campaigns",
      sa.Column("id", sa.Integer, primary_key=True),

      sa.Column(
          "brand_id",
          sa.Integer,
          sa.ForeignKey("brands.id", ondelete="CASCADE"),
          nullable=False,
      ),

      sa.Column("name", sa.String(255), nullable=False),
      sa.Column("target_region", sa.String(255), nullable=True),
      sa.Column("target_audience", sa.Text, nullable=True),
      sa.Column("campaign_message", sa.Text, nullable=False),
      sa.Column("localized_campaign_message", sa.Text, nullable=True),

      sa.Column(
          "created_at",
          sa.DateTime(timezone=True),
          server_default=func.now(),
          nullable=False,
      ),
      sa.Column(
          "updated_at",
          sa.DateTime(timezone=True),
          server_default=func.now(),
          onupdate=func.now(),
          nullable=False,
      ),
  )

  op.create_index(
      "ix_campaigns_brand_id",
      "campaigns",
      ["brand_id"],
  )
  op.create_index(
      "ix_campaigns_status",
      "campaigns",
      ["status"],
  )


def downgrade():
  op.drop_index("ix_campaigns_status", table_name="campaigns")
  op.drop_index("ix_campaigns_brand_id", table_name="campaigns")
  op.drop_table("campaigns")
