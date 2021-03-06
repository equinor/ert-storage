"""Remove record class

Revision ID: d72e51c6bdf2
Revises: 9064db29af73
Create Date: 2021-03-10 10:34:45.613538

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d72e51c6bdf2"
down_revision = "9064db29af73"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("ensemble", sa.Column("inputs", sa.ARRAY(sa.String()), nullable=True))
    op.add_column("record", sa.Column("ensemble_id", sa.Integer(), nullable=True))
    op.drop_constraint("record_consumer_id_fkey", "record", type_="foreignkey")
    op.drop_constraint("record_producer_id_fkey", "record", type_="foreignkey")
    op.create_foreign_key(None, "record", "ensemble", ["ensemble_id"], ["id"])
    op.drop_column("record", "consumer_id")
    op.drop_column("record", "producer_id")
    op.drop_column("record", "record_class")
    op.execute("DROP TYPE recordclass")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "record",
        sa.Column(
            "record_class",
            postgresql.ENUM("normal", "response", "parameter", name="recordclass"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "record",
        sa.Column("producer_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "record",
        sa.Column("consumer_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.drop_constraint(None, "record", type_="foreignkey")
    op.create_foreign_key(
        "record_producer_id_fkey", "record", "ensemble", ["producer_id"], ["id"]
    )
    op.create_foreign_key(
        "record_consumer_id_fkey", "record", "ensemble", ["consumer_id"], ["id"]
    )
    op.drop_column("record", "ensemble_id")
    op.drop_column("ensemble", "inputs")
    # ### end Alembic commands ###
