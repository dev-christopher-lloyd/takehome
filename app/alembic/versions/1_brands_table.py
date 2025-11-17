from alembic import op
import sqlalchemy as sa

revision = "1_brands_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
  op.create_table(
      "brands",
      sa.Column("id", sa.Integer, primary_key=True),
      sa.Column("name", sa.String(255), nullable=False),

      sa.Column("primary_color_hex", sa.String(7), nullable=False),
      sa.Column("secondary_color_hex", sa.String(7), nullable=True),

      sa.Column("tone_of_voice", sa.Text, nullable=True),
      sa.Column("font_family", sa.String(128), nullable=True),

      sa.Column(
          "created_at",
          sa.DateTime(timezone=True),
          server_default=sa.func.now(),
          nullable=False,
      ),
      sa.Column(
          "updated_at",
          sa.DateTime(timezone=True),
          server_default=sa.func.now(),
          onupdate=sa.func.now(),
          nullable=False,
      ),
  )


def downgrade():
  op.drop_table("brands")
