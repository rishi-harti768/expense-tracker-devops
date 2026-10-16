from alembic import op
import sqlalchemy as sa

revision = "0001_create_expenses"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False, server_default="OTHER"),
        sa.Column("spent_on", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

def downgrade():
    op.drop_table("expenses")
