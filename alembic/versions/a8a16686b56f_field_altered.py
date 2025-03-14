"""field altered

Revision ID: a8a16686b56f
Revises: 0d29fad93bb1
Create Date: 2025-02-19 10:50:51.494534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8a16686b56f'
down_revision: Union[str, None] = '0d29fad93bb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('user_security_questions_question_id_fkey', 'user_security_questions', type_='foreignkey')
    op.drop_constraint('user_security_questions_user_id_fkey', 'user_security_questions', type_='foreignkey')
    op.create_foreign_key(None, 'user_security_questions', 'security_questions', ['question_id'], ['id'], source_schema='risk', ondelete='CASCADE')
    op.create_foreign_key(None, 'user_security_questions', 'users', ['user_id'], ['id'], source_schema='risk', ondelete='CASCADE')
    op.alter_column('users', 'first_name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'last_name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'last_name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'first_name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_constraint(None, 'user_security_questions', schema='risk', type_='foreignkey')
    op.drop_constraint(None, 'user_security_questions', schema='risk', type_='foreignkey')
    op.create_foreign_key('user_security_questions_user_id_fkey', 'user_security_questions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_security_questions_question_id_fkey', 'user_security_questions', 'security_questions', ['question_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###
