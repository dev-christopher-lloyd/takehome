from alembic import op
import sqlalchemy as sa

revision = "3_legal_rules_table"
down_revision = "2_brand_rules_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "legal_rules",
        sa.Column("id", sa.Integer, primary_key=True),

        sa.Column(
            "brand_id",
            sa.Integer,
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=True,  # NULL => global rule
        ),

        # Stored as Integer, mapped to IntEnum in the model
        sa.Column("rule_type", sa.Integer, nullable=False),

        sa.Column("pattern", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),

        # Stored as Integer, mapped to IntEnum in the model
        sa.Column("severity", sa.Integer, nullable=False),
    )

    op.create_index(
        "ix_legal_rules_brand_id",
        "legal_rules",
        ["brand_id"],
    )
    op.create_index(
        "ix_legal_rules_rule_type",
        "legal_rules",
        ["rule_type"],
    )


def downgrade():
    op.drop_index("ix_legal_rules_rule_type", table_name="legal_rules")
    op.drop_index("ix_legal_rules_brand_id", table_name="legal_rules")
    op.drop_table("legal_rules")
