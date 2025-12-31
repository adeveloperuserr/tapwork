"""fix audit_logs foreign key to SET NULL

Revision ID: 0003
Revises: 0002
Create Date: 2025-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Eliminar la foreign key constraint existente
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')

    # Crear nueva foreign key constraint con ondelete SET NULL
    op.create_foreign_key(
        'audit_logs_user_id_fkey',
        'audit_logs',
        'users',
        ['user_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Revertir: eliminar la nueva constraint
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')

    # Recrear la constraint original sin ondelete
    op.create_foreign_key(
        'audit_logs_user_id_fkey',
        'audit_logs',
        'users',
        ['user_id'],
        ['id']
    )
