"""fix uq_ligne_run_num add id_feuille

Revision ID: c0a5c285ecbe
Revises: a3187e43649b
Create Date: 2026-10-29 11:26:49.759103

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = 'c0a5c285ecbe'
down_revision: str | None = 'a3187e43649b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Supprimer l'ancienne contrainte
    op.drop_constraint('uq_ligne_run_num', 'ligne_ingeree', type_='unique')
    # Ajouter la nouvelle contrainte avec id_feuille
    op.create_unique_constraint(
        'uq_ligne_feuille_run_num',
        'ligne_ingeree',
        ['id_feuille', 'id_run', 'num_ligne_source'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_ligne_feuille_run_num', 'ligne_ingeree', type_='unique')
    op.create_unique_constraint(
        'uq_ligne_run_num',
        'ligne_ingeree',
        ['id_run', 'num_ligne_source'],
    )