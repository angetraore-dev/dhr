"""refactor ouvrage + fix vue v_points_consolides

Revision ID: 478a8e09c628
Revises: 11834f4c8aa4
Create Date: ...
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '478a8e09c628'
down_revision: str | None = '11834f4c8aa4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Supprimer la vue qui dépend de id_type_ouvrage
    op.execute("DROP VIEW IF EXISTS v_points_consolides")

    # 2. Ajouter les nouvelles colonnes à ouvrage
    op.add_column('ouvrage', sa.Column('nature_ouvrage', sa.String(20), nullable=True))
    op.add_column('ouvrage', sa.Column('type_alimentation', sa.String(20), nullable=True))
    op.add_column('ouvrage', sa.Column('realisation_par', sa.String(20), nullable=True))

    op.create_check_constraint(
        'ouvrage_nature_check', 'ouvrage',
        "nature_ouvrage IS NULL OR nature_ouvrage IN ('puits','forage','inconnu')"
    )
    op.create_check_constraint(
        'ouvrage_alimentation_check', 'ouvrage',
        "type_alimentation IS NULL OR type_alimentation IN ('PMH','HVA','PEA','HV','AUTRE')"
    )
    op.create_check_constraint(
        'ouvrage_realisation_check', 'ouvrage',
        "realisation_par IS NULL OR realisation_par IN ('public','prive','inconnu')"
    )

    op.create_index('idx_ouvrage_nature', 'ouvrage', ['nature_ouvrage'])
    op.create_index('idx_ouvrage_alimentation', 'ouvrage', ['type_alimentation'])
    op.create_index('idx_ouvrage_realisation', 'ouvrage', ['realisation_par'])

    # 3. Supprimer l'ancienne FK et la colonne id_type_ouvrage
    op.drop_constraint('ouvrage_id_type_ouvrage_fkey', 'ouvrage', type_='foreignkey')
    op.drop_column('ouvrage', 'id_type_ouvrage')

    # 4. Supprimer la table type_ouvrage
    op.drop_table('type_ouvrage')

    # 5. Recréer la vue v_points_consolides avec les nouveaux champs
    op.execute("""
        CREATE OR REPLACE VIEW v_points_consolides AS
        SELECT
            o.id_ouvrage,
            o.code_ouvrage,
            o.etat,
            o.nature_ouvrage,
            o.type_alimentation,
            o.realisation_par,
            o.annee_realisation,
            l.nom_usage AS localite,
            g.nom AS sous_prefecture,
            gp.nom AS departement,
            gr.nom AS region,
            gd.nom AS district,
            o.latitude_decimal,
            o.longitude_decimal,
            o.geom
        FROM ouvrage o
        JOIN localite l ON l.id_localite = o.id_localite
        JOIN ref_geo_admin g ON g.id_geo = l.id_geo
        LEFT JOIN ref_geo_admin gp ON gp.id_geo = g.parent_id
        LEFT JOIN ref_geo_admin gr ON gr.id_geo = gp.parent_id
        LEFT JOIN ref_geo_admin gd ON gd.id_geo = gr.parent_id
        WHERE o.geom IS NOT NULL
    """)


def downgrade() -> None:
    # 1. Supprimer la vue recréée
    op.execute("DROP VIEW IF EXISTS v_points_consolides")

    # 2. Recréer la table type_ouvrage (simplifiée)
    op.create_table(
        'type_ouvrage',
        sa.Column('id_type_ouvrage', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True),
        sa.Column('libelle', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('actif', sa.Boolean(), server_default='true', nullable=False),
    )

    # 3. Ajouter id_type_ouvrage à ouvrage
    op.add_column('ouvrage', sa.Column('id_type_ouvrage', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'ouvrage_id_type_ouvrage_fkey', 'ouvrage', 'type_ouvrage',
        ['id_type_ouvrage'], ['id_type_ouvrage']
    )

    # 4. Supprimer les nouveaux index et colonnes
    op.drop_index('idx_ouvrage_realisation', table_name='ouvrage')
    op.drop_index('idx_ouvrage_alimentation', table_name='ouvrage')
    op.drop_index('idx_ouvrage_nature', table_name='ouvrage')
    op.drop_constraint('ouvrage_realisation_check', 'ouvrage', type_='check')
    op.drop_constraint('ouvrage_alimentation_check', 'ouvrage', type_='check')
    op.drop_constraint('ouvrage_nature_check', 'ouvrage', type_='check')
    op.drop_column('ouvrage', 'realisation_par')
    op.drop_column('ouvrage', 'type_alimentation')
    op.drop_column('ouvrage', 'nature_ouvrage')

    # 5. Recréer l'ancienne vue v_points_consolides
    op.execute("""
        CREATE OR REPLACE VIEW v_points_consolides AS
        SELECT
            o.id_ouvrage,
            o.code_ouvrage,
            o.etat,
            t.code AS type_ouvrage,
            o.annee_realisation,
            l.nom_usage AS localite,
            g.nom AS sous_prefecture,
            gp.nom AS departement,
            gr.nom AS region,
            gd.nom AS district,
            o.latitude_decimal,
            o.longitude_decimal,
            o.geom
        FROM ouvrage o
        JOIN type_ouvrage t ON t.id_type_ouvrage = o.id_type_ouvrage
        JOIN localite l ON l.id_localite = o.id_localite
        JOIN ref_geo_admin g ON g.id_geo = l.id_geo
        LEFT JOIN ref_geo_admin gp ON gp.id_geo = g.parent_id
        LEFT JOIN ref_geo_admin gr ON gr.id_geo = gp.parent_id
        LEFT JOIN ref_geo_admin gd ON gd.id_geo = gr.parent_id
        WHERE o.geom IS NOT NULL
    """)