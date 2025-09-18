"""add category to product

Revision ID: 634c05f74637
Revises: 4e9035e8d0d1
Create Date: 2025-09-15 08:03:26.610524

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '634c05f74637'
down_revision = '4e9035e8d0d1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'product',
        sa.Column('category', sa.String(length=128), nullable=True)
    )

def downgrade():
    op.drop_column('product', 'category')

    # ### end Alembic commands ###
