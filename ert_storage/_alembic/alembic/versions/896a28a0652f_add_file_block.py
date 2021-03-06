"""Add file block

Revision ID: 896a28a0652f
Revises: c1b95721c62a
Create Date: 2021-03-24 11:56:27.012796

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "896a28a0652f"
down_revision = "c1b95721c62a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "file_block",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "time_created",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "time_updated",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("block_id", sa.String(), nullable=False),
        sa.Column("block_index", sa.Integer(), nullable=False),
        sa.Column("record_name", sa.String(), nullable=False),
        sa.Column("realization_index", sa.Integer(), nullable=True),
        sa.Column("ensemble_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.LargeBinary(), nullable=True),
        sa.ForeignKeyConstraint(
            ["ensemble_id"],
            ["ensemble.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("file_block")
    # ### end Alembic commands ###
