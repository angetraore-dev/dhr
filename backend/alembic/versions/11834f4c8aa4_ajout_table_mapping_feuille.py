"""ajout table mapping_feuille

Revision ID: 11834f4c8aa4
Revises: bfe7f0a52802
Create Date: 2026-11-02 10:52:35.851614

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = '11834f4c8aa4'
down_revision: str | None = 'bfe7f0a52802'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'mapping_feuille',
        sa.Column('id_mapping', sa.Integer(), nullable=False),
        sa.Column('id_feuille', sa.BigInteger(), nullable=False),
        sa.Column('entete_brut', sa.String(length=255), nullable=False),
        sa.Column('champ_cible', sa.String(length=100), nullable=True),
        sa.Column('confiance', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('valide_par_utilisateur', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            'confiance IS NULL OR (confiance >= 0 AND confiance <= 1)',
            name='mapping_feuille_confiance_check',
        ),
        sa.ForeignKeyConstraint(['id_feuille'], ['feuille.id_feuille'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_mapping'),
        sa.UniqueConstraint('id_feuille', 'entete_brut', name='uq_mapping_feuille_entete'),
    )
    op.create_index('idx_mapping_feuille_feuille', 'mapping_feuille', ['id_feuille'])

def downgrade() -> None:
    op.drop_index('idx_mapping_feuille_feuille', table_name='mapping_feuille')
    op.drop_table('mapping_feuille')