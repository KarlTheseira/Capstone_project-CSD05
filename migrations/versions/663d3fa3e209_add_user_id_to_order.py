"""add user_id to order

Revision ID: 663d3fa3e209
Revises: 634c05f74637
Create Date: 2025-09-16 06:57:24.830195

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '663d3fa3e209'
down_revision = '634c05f74637'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_order_user',
            'user',
            ['user_id'],
            ['id']
        )

def downgrade():
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_constraint('fk_order_user', type_='foreignkey')
        batch_op.drop_column('user_id')

