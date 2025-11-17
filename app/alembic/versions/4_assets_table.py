from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

revision = "4_assets_table"          
down_revision = "3_products_table"     
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
      "assets",
      sa.Column("id", sa.Integer, primary_key=True),

    sa.Column(
        "brand_id",
        sa.Integer,
        sa.ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=True,
      ),

      sa.Column(
          "campaign_id",
          sa.Integer,
          sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
          nullable=True,
      ),

      sa.Column(
          "product_id",
          sa.Integer,
          sa.ForeignKey("products.id", ondelete="CASCADE"),
          nullable=True,
      ),

      sa.Column("type", sa.Integer, nullable=False),

      sa.Column("aspect_ratio", sa.String(16), nullable=True),

      sa.Column("width", sa.Integer, nullable=True),
      sa.Column("height", sa.Integer, nullable=True),

      sa.Column("s3_key", sa.String(255), nullable=False),

      sa.Column("source", sa.Integer, nullable=False),

      sa.Column("gen_metadata_json", postgresql.JSONB, nullable=True),

      sa.Column(
          "created_at",
          sa.DateTime(timezone=True),
          server_default=func.now(),
          nullable=False,
      ),
  )

  op.create_index(
      "ix_assets_brand_id",
      "assets",
      ["brand_id"],
  )
  op.create_index(
      "ix_assets_campaign_id",
      "assets",
      ["campaign_id"],
  )
  op.create_index(
      "ix_assets_product_id",
      "assets",
      ["product_id"],
  )
  op.create_index(
      "ix_assets_type",
      "assets",
      ["type"],
  )
  op.create_index(
      "ix_assets_source",
      "assets",
      ["source"],
  )


def downgrade():
  op.drop_index("ix_assets_source", table_name="assets")
  op.drop_index("ix_assets_type", table_name="assets")
  op.drop_index("ix_assets_product_id", table_name="assets")
  op.drop_index("ix_assets_campaign_id", table_name="assets")
  op.drop_index("ix_assets_brand_id", table_name="assets")
  op.drop_table("assets")
