from alembic import op
import sqlalchemy as sa

revision = "2_brand_rules_table"
down_revision = "1_brands_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "brand_rules",
        sa.Column("id", sa.Integer, primary_key=True),

        sa.Column(
            "brand_id",
            sa.Integer,
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # Stored as Integer, mapped to Python IntEnum in the model
        sa.Column("rule_type", sa.Integer, nullable=False),

        sa.Column("config_json", sa.JSON, nullable=True),

        # Stored as Integer, mapped to Python IntEnum in the model
        sa.Column("severity", sa.Integer, nullable=False),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_brand_rules_brand_id",
        "brand_rules",
        ["brand_id"],
    )
    op.create_index(
        "ix_brand_rules_rule_type",
        "brand_rules",
        ["rule_type"],
    )


def downgrade():
    op.drop_index("ix_brand_rules_rule_type", table_name="brand_rules")
    op.drop_index("ix_brand_rules_brand_id", table_name="brand_rules")
    op.drop_table("brand_rules")
