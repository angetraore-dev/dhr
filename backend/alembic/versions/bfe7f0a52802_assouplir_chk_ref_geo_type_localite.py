"""assouplir chk_ref_geo_type_localite

Revision ID: bfe7f0a52802
Revises: c0a5c285ecbe
Create Date: 2026-10-30 11:58:07.941236

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = 'bfe7f0a52802'
down_revision: str | None = 'c0a5c285ecbe'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint('chk_ref_geo_type_localite', 'ref_geo_admin', type_='check')
    # Nouvelle contrainte :
    # - type_localite NULL autorisé pour tous les niveaux (y compris localite)
    # - type_localite NOT NULL interdit pour les niveaux non-localite
    op.create_check_constraint(
        'chk_ref_geo_type_localite',
        'ref_geo_admin',
        "(niveau <> 'localite' AND type_localite IS NULL) "
        "OR (niveau = 'localite')"
    )


def downgrade() -> None:
    op.drop_constraint('chk_ref_geo_type_localite', 'ref_geo_admin', type_='check')
    op.create_check_constraint(
        'chk_ref_geo_type_localite',
        'ref_geo_admin',
        "(niveau = 'localite' AND type_localite IS NOT NULL) "
        "OR (niveau <> 'localite' AND type_localite IS NULL)"
    )