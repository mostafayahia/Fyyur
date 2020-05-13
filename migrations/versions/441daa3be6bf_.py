"""empty message

Revision ID: 441daa3be6bf
Revises: db149f9f0568
Create Date: 2020-05-11 10:56:45.812240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '441daa3be6bf'
down_revision = 'db149f9f0568'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('shows_pkey', 'shows', type_='primary')
    op.create_primary_key('pk_venueid_artistid_starttime', 'shows', ['venue_id', 'artist_id', 'start_time'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('pk_venueid_artistid_starttime', 'shows', type_='primary')
    op.create_primary_key('shows_pkey', 'shows', ['venue_id', 'artist_id'])
    # ### end Alembic commands ###
