"""miror changes in db

Revision ID: 9413ed67678c
Revises: 02b99cb13a20
Create Date: 2024-01-27 00:37:25.920995

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9413ed67678c'
down_revision = '02b99cb13a20'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('teacher_class')
    op.drop_table('student_class')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('student_class',
    sa.Column('student_id', sa.INTEGER(), nullable=False),
    sa.Column('class_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['class_id'], ['class.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('student_id', 'class_id')
    )
    op.create_table('teacher_class',
    sa.Column('teacher_id', sa.INTEGER(), nullable=False),
    sa.Column('class_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['class_id'], ['class.id'], ),
    sa.ForeignKeyConstraint(['teacher_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('teacher_id', 'class_id')
    )
    # ### end Alembic commands ###
