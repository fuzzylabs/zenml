"""Add Artifact Metadata [90a347b0fae1].

Revision ID: 90a347b0fae1
Revises: 248dfd320b68
Create Date: 2022-12-07 12:01:30.001826

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "90a347b0fae1"
down_revision = "248dfd320b68"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema and/or data, creating a new revision."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("artifact", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("artifact_metadata", sa.TEXT(), nullable=True)
        )
    with op.batch_alter_table("pipeline_run", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("enable_artifact_metadata", sa.Boolean(), nullable=True)
        )

    with op.batch_alter_table("step_run", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("enable_artifact_metadata", sa.Boolean(), nullable=True)
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade database schema and/or data back to the previous revision."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("step_run", schema=None) as batch_op:
        batch_op.drop_column("enable_artifact_metadata")

    with op.batch_alter_table("pipeline_run", schema=None) as batch_op:
        batch_op.drop_column("enable_artifact_metadata")

    with op.batch_alter_table("artifact", schema=None) as batch_op:
        batch_op.drop_column("artifact_metadata")

    # ### end Alembic commands ###
