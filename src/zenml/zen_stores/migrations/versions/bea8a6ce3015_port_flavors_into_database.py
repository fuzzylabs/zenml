"""Port flavors into database. [bea8a6ce3015].

Revision ID: bea8a6ce3015
Revises: 0.32.0
Create Date: 2022-12-20 11:20:30.731406

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bea8a6ce3015"
down_revision = "0.32.0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema and/or data, creating a new revision."""
    with op.batch_alter_table("flavor", schema=None) as batch_op:

        batch_op.add_column(sa.Column("logo_url", sa.TEXT(), nullable=True))
        batch_op.add_column(
            sa.Column("flavor_docs_url", sa.TEXT(), nullable=True)
        )

        batch_op.alter_column(
            "project_id", existing_type=sa.CHAR(length=32), nullable=True
        )

        batch_op.alter_column(
            "user_id", existing_type=sa.CHAR(length=32), nullable=True
        )


def downgrade() -> None:
    """Downgrade database schema and/or data back to the previous revision."""
    with op.batch_alter_table("flavor", schema=None) as batch_op:

        batch_op.drop_column("logo_url")

        # TODO: all columns that don't conform to this will need to be dropped
        batch_op.alter_column(
            "project_id", existing_type=sa.CHAR(length=32), nullable=False
        )

        batch_op.alter_column(
            "user_id", existing_type=sa.CHAR(length=32), nullable=False
        )
