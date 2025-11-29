"""create saved_searches table

Revision ID: 79cc73b627c8
Revises: a0a283f28ab8
Create Date: 2025-11-29 09:49:49.626535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79cc73b627c8'
down_revision: Union[str, None] = 'a0a283f28ab8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
