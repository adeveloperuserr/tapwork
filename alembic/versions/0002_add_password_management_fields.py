"""add password management fields

Revision ID: 0002
Revises: 0001_initial
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password management fields to users table
    op.add_column('users', sa.Column('password_reset_required', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))

    # Create index for password reset token
    op.create_index('ix_users_password_reset_token', 'users', ['password_reset_token'], unique=False)


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_users_password_reset_token', table_name='users')

    # Remove columns
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'password_reset_required')
