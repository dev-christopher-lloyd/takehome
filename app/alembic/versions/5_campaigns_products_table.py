from alembic import op
import sqlalchemy as sa

revision = "5_campaigns_products_table"
down_revision = "4_assets_table"
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
      "campaign_products",
      sa.Column(
          "campaign_id",
          sa.Integer,
          sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
          nullable=False,
      ),
      sa.Column(
          "product_id",
          sa.Integer,
          sa.ForeignKey("products.id", ondelete="CASCADE"),
          nullable=False,
      ),
      sa.PrimaryKeyConstraint("campaign_id", "product_id",
                              name="pk_campaign_products"),
  )

  op.create_index(
      "ix_campaign_products_campaign_id",
      "campaign_products",
      ["campaign_id"],
  )
  op.create_index(
      "ix_campaign_products_product_id",
      "campaign_products",
      ["product_id"],
  )


def downgrade():
  op.drop_index("ix_campaign_products_product_id",
                table_name="campaign_products")
  op.drop_index("ix_campaign_products_campaign_id",
                table_name="campaign_products")
  op.drop_table("campaign_products")
