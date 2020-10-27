"""first load

Revision ID: d10c4d8d4690
Revises: 29d6fc4c840e
Create Date: 2020-03-02 06:42:07.634507

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd10c4d8d4690'
down_revision = '29d6fc4c840e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tor_exit_node',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ip_address', sa.String(), nullable=False),
    sa.Column('fingerprint', sa.String(), nullable=False),
    sa.Column('nickname', sa.String(), nullable=False),
    sa.Column('updated', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fingerprint'),
    sa.UniqueConstraint('fingerprint', name='fingerprint_constraint')
    )
    op.create_table('useragent',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('useragent', sa.String(), nullable=False),
    sa.Column('browser_version', sa.String(), nullable=False),
    sa.Column('browser_name', sa.String(), nullable=False),
    sa.Column('platform', sa.String(), nullable=False),
    sa.Column('updated', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('useragent'),
    sa.UniqueConstraint('useragent', name='useragent_constraint')
    )
    op.create_table('tor_exit_node_useragent',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('website', sa.String(), nullable=False),
    sa.Column('blocked', sa.Boolean(), nullable=False),
    sa.Column('updated', sa.Date(), nullable=True),
    sa.Column('useragent_id', sa.Integer(), nullable=True),
    sa.Column('tor_exit_node_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['tor_exit_node_id'], ['tor_exit_node.id'], ),
    sa.ForeignKeyConstraint(['useragent_id'], ['useragent.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('website', 'tor_exit_node_id', name='website_tor_constraint')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tor_exit_node_useragent')
    op.drop_table('useragent')
    op.drop_table('tor_exit_node')
    # ### end Alembic commands ###