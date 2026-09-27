"""prepare existing accounts for Telegram authentication

Revision ID: d9417b2e6a30
Revises: 8b31a6d24f90
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd9417b2e6a30'
down_revision: Union[str, Sequence[str], None] = '8b31a6d24f90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NULL means an existing account has not been linked yet. Multiple NULLs
    # are allowed, but a Telegram identity can belong to only one account.
    # Duplicate non-NULL IDs deliberately fail the unique constraint rather
    # than silently unlinking or merging existing accounts.
    op.alter_column('users', 'tg_id', existing_type=sa.Integer(),
                    type_=sa.BigInteger(), existing_nullable=True)
    op.create_unique_constraint('uq_users_tg_id', 'users', ['tg_id'])
    op.add_column('users', sa.Column('is_active', sa.Boolean(),
                                    server_default=sa.true(), nullable=False))
    op.alter_column('users', 'telegram_login', existing_type=sa.String(),
                    nullable=True)
    op.alter_column('users', 'password_hash', existing_type=sa.String(),
                    nullable=True)


def downgrade() -> None:
    # PostgreSQL will reject this rollback if new accounts lack usernames or
    # passwords, or Telegram IDs exceed int32. Do not invent credentials,
    # truncate IDs or delete users to make an incompatible rollback succeed.
    op.alter_column('users', 'password_hash', existing_type=sa.String(),
                    nullable=False)
    op.alter_column('users', 'telegram_login', existing_type=sa.String(),
                    nullable=False)
    op.drop_column('users', 'is_active')
    op.drop_constraint('uq_users_tg_id', 'users', type_='unique')
    op.alter_column('users', 'tg_id', existing_type=sa.BigInteger(),
                    type_=sa.Integer(), existing_nullable=True)
