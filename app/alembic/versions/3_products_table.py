from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects import postgresql

revision = "3_products_table"
down_revision = "2_campaigns_table"
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
      "products",
      sa.Column("id", sa.Integer, primary_key=True),

      sa.Column("name", sa.String(255), nullable=False),
      sa.Column("description", sa.Text, nullable=True),

      sa.Column("metadata_json", postgresql.JSONB, nullable=True),

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


def downgrade():
  op.drop_table("products")
