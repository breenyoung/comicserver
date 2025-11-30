"""create system_settings table

Revision ID: a71d8abd598f
Revises: 79cc73b627c8
Create Date: 2025-11-30 11:50:21.441595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a71d8abd598f'
down_revision: Union[str, None] = '79cc73b627c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
