"""add stock to product

Revision ID: 4e9035e8d0d1
Revises: 
Create Date: 2025-09-15 06:26:22.624039

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e9035e8d0d1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # only add the stock column to product
    op.add_column(
        'product',
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0')
    )
    # remove server_default if you like, once existing rows have a value:
    # op.alter_column('product', 'stock', server_default=None)

def downgrade():
    # drop the stock column
    op.drop_column('product', 'stock')

    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###
