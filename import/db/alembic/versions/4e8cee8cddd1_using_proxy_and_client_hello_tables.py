"""using 'proxy' and 'client_hello' tables

Revision ID: 4e8cee8cddd1
Revises: 81968acd3f6d
Create Date: 2020-07-18 14:55:46.276835

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e8cee8cddd1'
down_revision = '81968acd3f6d'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('tor_exit_node_useragent_ja3_hash')
    op.drop_table('useragent_ja3_hash')
    op.drop_table('useragent')
    op.drop_table('tor_exit_node')
    op.drop_table('ja3_hash')

    op.create_table('client_hello',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('platform', sa.String(), nullable=False),
    sa.Column('source', sa.String(), nullable=False),
    sa.Column('client_hello', sa.String(), nullable=False),
    sa.Column('updated', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('client_hello'),
    sa.UniqueConstraint('client_hello', name='client_hello_constraint')
    )

    op.create_table('proxy',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ip_address', sa.String(), nullable=False),
    sa.Column('tor_fingerprint', sa.String(), nullable=True),
    sa.Column('tor_nickname', sa.String(), nullable=True),
    sa.Column('is_tor_exit_node', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tor_fingerprint'),
    sa.UniqueConstraint('ip_address', name='ip_address_constraint')
    )

    op.create_table('client_hello_proxy',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_hello_id', sa.Integer(), nullable=False),
    sa.Column('proxy_id', sa.Integer(), nullable=False),
    sa.Column('website', sa.String(), nullable=False),
    sa.Column('blocked', sa.Boolean(), nullable=False),
    sa.Column('updated', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['client_hello_id'], ['client_hello.id'], ),
    sa.ForeignKeyConstraint(['proxy_id'], ['proxy.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('website', 'proxy_id', name='website_proxy_constraint')
    )


def downgrade():
    pass
