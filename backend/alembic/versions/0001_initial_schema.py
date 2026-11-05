"""initial schema (consolidé)

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-05

Migration unique consolidant l'historique complet :
- Extensions PostgreSQL (postgis, fuzzystrmatch, unaccent, pg_trgm)
- Fonctions geom_from_latlon, trg_set_updated_at, trg_check_localite_geo
- 12 tables (sans type_ouvrage, refactor ouvrage intégré)
- Colonnes générées geom / geom_centre (GENERATED ALWAYS AS ... STORED)
- Champ qualite_eau JSONB nullable sur ouvrage (+ index GIN)
- Index GIST, GIN, trigram
- Triggers set_updated_at (7 tables), check_localite_geo (localite)
- Vues v_points_par_fichier, v_points_consolides, v_qualite_par_fichier
- Seed source
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =================================================================
    # 1. EXTENSIONS
    # =================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # =================================================================
    # 2. FONCTIONS
    # =================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION geom_from_latlon(
            lat double precision,
            lon double precision
        )
        RETURNS geometry(Point, 4326) AS $$
        BEGIN
            IF lat IS NULL OR lon IS NULL
               OR lat < -90 OR lat > 90
               OR lon < -180 OR lon > 180
               OR (lat = 0 AND lon = 0) THEN
                RETURN NULL;
            END IF;
            RETURN ST_SetSRID(ST_MakePoint(lon, lat), 4326);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE STRICT;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION trg_set_updated_at()
        RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION trg_check_localite_geo()
        RETURNS trigger AS $$
        DECLARE
            v_niveau varchar(20);
        BEGIN
            SELECT niveau INTO v_niveau FROM ref_geo_admin WHERE id_geo = NEW.id_geo;
            IF v_niveau IS DISTINCT FROM 'localite' THEN
                RAISE EXCEPTION
                    'localite.id_geo doit référencer un ref_geo_admin de niveau localite (reçu: %)',
                    COALESCE(v_niveau, 'introuvable');
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # =================================================================
    # 3. TABLES
    # =================================================================

    # ----- ref_geo_admin -----
    op.create_table('ref_geo_admin',
        sa.Column('id_geo', sa.Integer(), nullable=False),
        sa.Column('niveau', sa.String(length=20), nullable=False),
        sa.Column('nom', sa.String(length=150), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('code_officiel', sa.String(length=50), nullable=True),
        sa.Column('type_localite', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "(niveau = 'district' AND parent_id IS NULL) OR (niveau <> 'district' AND parent_id IS NOT NULL)",
            name='chk_ref_geo_parent',
        ),
        sa.CheckConstraint(
            "(niveau <> 'localite' AND type_localite IS NULL) OR (niveau = 'localite')",
            name='chk_ref_geo_type_localite',
        ),
        sa.CheckConstraint(
            "niveau IN ('district','region','departement','sous_prefecture','localite')",
            name='ref_geo_admin_niveau_check',
        ),
        sa.CheckConstraint(
            "type_localite IS NULL OR type_localite IN ('village','campement','autre')",
            name='ref_geo_admin_type_localite_check',
        ),
        sa.ForeignKeyConstraint(['parent_id'], ['ref_geo_admin.id_geo'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id_geo'),
        sa.UniqueConstraint('parent_id', 'nom', 'niveau', name='uq_ref_geo_parent_nom_niveau'),
    )
    op.create_index('idx_ref_geo_niveau', 'ref_geo_admin', ['niveau'])
    op.create_index('idx_ref_geo_parent', 'ref_geo_admin', ['parent_id'])
    op.execute("CREATE INDEX idx_ref_geo_nom_trgm ON ref_geo_admin USING gin (nom gin_trgm_ops)")

    # ----- source -----
    op.create_table('source',
        sa.Column('id_source', sa.Integer(), nullable=False),
        sa.Column('nom', sa.String(length=100), nullable=False),
        sa.Column('type_source', sa.String(length=30), nullable=False),
        sa.Column('actif', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "type_source IN ('public','prive','bailleur','etat','autre')",
            name='source_type_source_check',
        ),
        sa.PrimaryKeyConstraint('id_source'),
        sa.UniqueConstraint('nom'),
    )

    # ----- fichier -----
    op.create_table('fichier',
        sa.Column('id_fichier', sa.BigInteger(), nullable=False),
        sa.Column('id_source', sa.Integer(), nullable=False),
        sa.Column('nom_fichier_original', sa.String(length=255), nullable=False),
        sa.Column('chemin_stockage', sa.Text(), nullable=False),
        sa.Column('hash_sha256', sa.String(length=64), nullable=True),
        sa.Column('taille_octets', sa.BigInteger(), nullable=True),
        sa.Column('date_reception', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('date_ingestion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=False),
        sa.Column('nb_feuilles', sa.Integer(), server_default='0', nullable=False),
        sa.Column('nb_lignes_total', sa.Integer(), server_default='0', nullable=False),
        sa.Column('est_reingestion', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "statut IN ('en_attente','en_cours','ingere','partiel','erreur')",
            name='fichier_statut_check',
        ),
        sa.ForeignKeyConstraint(['id_source'], ['source.id_source'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id_fichier'),
    )
    op.create_index('idx_fichier_date', 'fichier', ['date_reception'])
    op.create_index('idx_fichier_hash', 'fichier', ['hash_sha256'])
    op.create_index('idx_fichier_source', 'fichier', ['id_source'])

    # ----- localite -----
    op.create_table('localite',
        sa.Column('id_localite', sa.Integer(), nullable=False),
        sa.Column('id_geo', sa.Integer(), nullable=False),
        sa.Column('nom_usage', sa.String(length=150), nullable=False),
        sa.Column('latitude_centre', sa.Float(), nullable=True),
        sa.Column('longitude_centre', sa.Float(), nullable=True),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id_geo'], ['ref_geo_admin.id_geo'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id_localite'),
    )
    op.execute("""
        ALTER TABLE localite
        ADD COLUMN geom_centre geometry(Point,4326)
        GENERATED ALWAYS AS (geom_from_latlon(latitude_centre, longitude_centre)) STORED
    """)
    op.create_index('idx_localite_geo', 'localite', ['id_geo'])
    op.create_index('idx_localite_metadata', 'localite', ['metadata'], postgresql_using='gin')
    op.execute("CREATE INDEX idx_localite_geom ON localite USING gist (geom_centre)")
    op.execute("CREATE INDEX idx_localite_nom_trgm ON localite USING gin (nom_usage gin_trgm_ops)")

    # ----- localite_alias -----
    op.create_table('localite_alias',
        sa.Column('id_alias', sa.Integer(), nullable=False),
        sa.Column('id_localite', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(length=150), nullable=False),
        sa.Column('source_alias', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['id_localite'], ['localite.id_localite'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_alias'),
        sa.UniqueConstraint('id_localite', 'alias', name='uq_alias_localite'),
    )
    op.execute("CREATE INDEX idx_alias_trgm ON localite_alias USING gin (alias gin_trgm_ops)")

    # ----- projet_financement -----
    op.create_table('projet_financement',
        sa.Column('id_projet', sa.BigInteger(), nullable=False),
        sa.Column('nom_projet', sa.String(length=255), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=True),
        sa.Column('id_source_financeur', sa.Integer(), nullable=False),
        sa.Column('type_financement', sa.String(length=20), nullable=False),
        sa.Column('montant', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('devise', sa.String(length=3), server_default='XOF', nullable=True),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "type_financement IN ('etat','prive','partenariat','inconnu')",
            name='projet_financement_type_check',
        ),
        sa.ForeignKeyConstraint(['id_source_financeur'], ['source.id_source'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id_projet'),
    )
    op.create_index('idx_projet_annee', 'projet_financement', ['annee'])
    op.create_index('idx_projet_source', 'projet_financement', ['id_source_financeur'])

    # ----- feuille -----
    op.create_table('feuille',
        sa.Column('id_feuille', sa.BigInteger(), nullable=False),
        sa.Column('id_fichier', sa.BigInteger(), nullable=False),
        sa.Column('nom_feuille', sa.String(length=150), nullable=False),
        sa.Column('index_feuille', sa.Integer(), nullable=False),
        sa.Column('type_contenu', sa.String(length=20), nullable=False),
        sa.Column('nb_lignes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('nb_lignes_valides', sa.Integer(), server_default='0', nullable=False),
        sa.Column('statut_ingestion', sa.String(length=20), nullable=False),
        sa.Column('message_erreur', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "statut_ingestion IN ('en_attente','en_cours','ingere','partiel','erreur')",
            name='feuille_statut_ingestion_check',
        ),
        sa.CheckConstraint(
            "type_contenu IN ('ouvrages','cgpe','mixte','autre','inconnu')",
            name='feuille_type_contenu_check',
        ),
        sa.ForeignKeyConstraint(['id_fichier'], ['fichier.id_fichier'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_feuille'),
        sa.UniqueConstraint('id_fichier', 'index_feuille', name='uq_feuille_fichier_index'),
    )
    op.create_index('idx_feuille_fichier', 'feuille', ['id_fichier'])

    # ----- mapping_feuille -----
    op.create_table('mapping_feuille',
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

    # ----- ouvrage -----
    op.create_table('ouvrage',
        sa.Column('id_ouvrage', sa.BigInteger(), nullable=False),
        sa.Column('code_ouvrage', sa.String(length=100), nullable=True),
        sa.Column('id_localite', sa.Integer(), nullable=False),
        sa.Column('nature_ouvrage', sa.String(length=20), nullable=True),
        sa.Column('type_alimentation', sa.String(length=20), nullable=True),
        sa.Column('realisation_par', sa.String(length=20), nullable=True),
        sa.Column('etat', sa.String(length=20), nullable=False),
        sa.Column('annee_realisation', sa.Integer(), nullable=True),
        sa.Column('latitude_decimal', sa.Float(), nullable=True),
        sa.Column('longitude_decimal', sa.Float(), nullable=True),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('qualite_eau', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "nature_ouvrage IS NULL OR nature_ouvrage IN ('puits','forage','inconnu')",
            name='ouvrage_nature_check',
        ),
        sa.CheckConstraint(
            "type_alimentation IS NULL OR type_alimentation IN ('PMH','HVA','PEA','HV','AUTRE')",
            name='ouvrage_alimentation_check',
        ),
        sa.CheckConstraint(
            "realisation_par IS NULL OR realisation_par IN ('public','prive','inconnu')",
            name='ouvrage_realisation_check',
        ),
        sa.CheckConstraint(
            "etat IN ('fonctionnel','en_panne','abandonne','inconnu')",
            name='ouvrage_etat_check',
        ),
        sa.ForeignKeyConstraint(['id_localite'], ['localite.id_localite'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id_ouvrage'),
    )
    op.execute("""
        ALTER TABLE ouvrage
        ADD COLUMN geom geometry(Point,4326)
        GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED
    """)
    op.create_index('idx_ouvrage_code', 'ouvrage', ['code_ouvrage'],
                    postgresql_where='code_ouvrage IS NOT NULL')
    op.create_index('idx_ouvrage_etat', 'ouvrage', ['etat'])
    op.create_index('idx_ouvrage_localite', 'ouvrage', ['id_localite'])
    op.create_index('idx_ouvrage_metadata', 'ouvrage', ['metadata'], postgresql_using='gin')
    op.create_index('idx_ouvrage_qualite_eau', 'ouvrage', ['qualite_eau'], postgresql_using='gin')
    op.create_index('idx_ouvrage_nature', 'ouvrage', ['nature_ouvrage'])
    op.create_index('idx_ouvrage_alimentation', 'ouvrage', ['type_alimentation'])
    op.create_index('idx_ouvrage_realisation', 'ouvrage', ['realisation_par'])
    op.execute("CREATE INDEX idx_ouvrage_geom ON ouvrage USING gist (geom)")

    # ----- cgpe -----
    op.create_table('cgpe',
        sa.Column('id_cgpe', sa.Integer(), nullable=False),
        sa.Column('id_localite', sa.Integer(), nullable=False),
        sa.Column('id_ouvrage', sa.BigInteger(), nullable=True),
        sa.Column('existe', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('date_creation', sa.Date(), nullable=True),
        sa.Column('statut', sa.String(length=20), nullable=True),
        sa.Column('nb_membres', sa.Integer(), nullable=True),
        sa.Column('commentaire', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "statut IS NULL OR statut IN ('fonctionnel','non_fonctionnel','inconnu')",
            name='cgpe_statut_check',
        ),
        sa.ForeignKeyConstraint(['id_localite'], ['localite.id_localite'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_ouvrage'], ['ouvrage.id_ouvrage'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id_cgpe'),
    )
    op.create_index('idx_cgpe_localite', 'cgpe', ['id_localite'])
    op.create_index('idx_cgpe_metadata', 'cgpe', ['metadata'], postgresql_using='gin')
    op.create_index('idx_cgpe_ouvrage', 'cgpe', ['id_ouvrage'])

    # ----- ingestion_run -----
    op.create_table('ingestion_run',
        sa.Column('id_run', sa.BigInteger(), nullable=False),
        sa.Column('id_fichier', sa.BigInteger(), nullable=False),
        sa.Column('id_feuille', sa.BigInteger(), nullable=True),
        sa.Column('mode', sa.String(length=20), nullable=False),
        sa.Column('limite_lignes', sa.Integer(), nullable=True),
        sa.Column('ligne_debut', sa.Integer(), nullable=True),
        sa.Column('ligne_fin', sa.Integer(), nullable=True),
        sa.Column('nb_lignes_ingerees', sa.Integer(), server_default='0', nullable=False),
        sa.Column('statut', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(mode = 'complet' AND limite_lignes IS NULL AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'echantillon' AND limite_lignes IS NOT NULL AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'plage' AND limite_lignes IS NULL AND ligne_debut IS NOT NULL AND ligne_fin IS NOT NULL AND ligne_fin >= ligne_debut)",
            name='chk_run_mode_params',
        ),
        sa.CheckConstraint("mode IN ('complet','echantillon','plage')", name='ingestion_run_mode_check'),
        sa.CheckConstraint(
            "statut IN ('en_cours','termine','erreur','annule')",
            name='ingestion_run_statut_check',
        ),
        sa.ForeignKeyConstraint(['id_feuille'], ['feuille.id_feuille'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_fichier'], ['fichier.id_fichier'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_run'),
    )
    op.create_index('idx_run_feuille', 'ingestion_run', ['id_feuille'])
    op.create_index('idx_run_fichier', 'ingestion_run', ['id_fichier'])
    op.create_index('idx_run_statut', 'ingestion_run', ['statut'])

    # ----- ligne_ingeree -----
    op.create_table('ligne_ingeree',
        sa.Column('id_ligne', sa.BigInteger(), nullable=False),
        sa.Column('id_feuille', sa.BigInteger(), nullable=False),
        sa.Column('id_run', sa.BigInteger(), nullable=True),
        sa.Column('num_ligne_source', sa.Integer(), nullable=False),
        sa.Column('donnees_brutes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('district_brut', sa.String(length=150), nullable=True),
        sa.Column('region_brute', sa.String(length=150), nullable=True),
        sa.Column('departement_brut', sa.String(length=150), nullable=True),
        sa.Column('sous_prefecture_brute', sa.String(length=150), nullable=True),
        sa.Column('localite_brute', sa.String(length=150), nullable=True),
        sa.Column('type_localite_brut', sa.String(length=30), nullable=True),
        sa.Column('latitude_decimal', sa.Float(), nullable=True),
        sa.Column('longitude_decimal', sa.Float(), nullable=True),
        sa.Column('type_ouvrage_brut', sa.String(length=50), nullable=True),
        sa.Column('etat_ouvrage_brut', sa.String(length=50), nullable=True),
        sa.Column('annee_projet', sa.Integer(), nullable=True),
        sa.Column('bailleur_brut', sa.String(length=150), nullable=True),
        sa.Column('type_financement_brut', sa.String(length=50), nullable=True),
        sa.Column('a_cgpe', sa.Boolean(), nullable=True),
        sa.Column('statut_qualite', sa.String(length=30), nullable=False),
        sa.Column('message_qualite', sa.Text(), nullable=True),
        sa.Column('id_localite', sa.Integer(), nullable=True),
        sa.Column('id_ouvrage_consolide', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "statut_qualite IN ('ok','localite_non_resolue','geom_invalide',"
            "'type_ouvrage_inconnu','rejete','doublon_suspect')",
            name='ligne_ingeree_statut_qualite_check',
        ),
        sa.ForeignKeyConstraint(['id_feuille'], ['feuille.id_feuille'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_localite'], ['localite.id_localite'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['id_ouvrage_consolide'], ['ouvrage.id_ouvrage'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['id_run'], ['ingestion_run.id_run'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id_ligne'),
        sa.UniqueConstraint('id_feuille', 'id_run', 'num_ligne_source', name='uq_ligne_feuille_run_num'),
    )
    op.execute("""
        ALTER TABLE ligne_ingeree
        ADD COLUMN geom geometry(Point,4326)
        GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED
    """)
    op.create_index('idx_ligne_donnees_brutes', 'ligne_ingeree', ['donnees_brutes'], postgresql_using='gin')
    op.create_index('idx_ligne_feuille', 'ligne_ingeree', ['id_feuille'])
    op.create_index('idx_ligne_localite', 'ligne_ingeree', ['id_localite'])
    op.create_index('idx_ligne_ouvrage', 'ligne_ingeree', ['id_ouvrage_consolide'])
    op.create_index('idx_ligne_run', 'ligne_ingeree', ['id_run'])
    op.create_index('idx_ligne_statut_qualite', 'ligne_ingeree', ['statut_qualite'])
    op.create_index('idx_ligne_type_ouvrage', 'ligne_ingeree', ['type_ouvrage_brut'])
    op.execute("CREATE INDEX idx_ligne_geom ON ligne_ingeree USING gist (geom)")

    # ----- ouvrage_projet -----
    op.create_table('ouvrage_projet',
        sa.Column('id_ouvrage', sa.BigInteger(), nullable=False),
        sa.Column('id_projet', sa.BigInteger(), nullable=False),
        sa.Column('role_financement', sa.String(length=20), nullable=False),
        sa.CheckConstraint(
            "role_financement IN ('principal','co_financement')",
            name='ouvrage_projet_role_check',
        ),
        sa.ForeignKeyConstraint(['id_ouvrage'], ['ouvrage.id_ouvrage'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_projet'], ['projet_financement.id_projet'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_ouvrage', 'id_projet'),
    )
    op.create_index('idx_ouvrage_projet_projet', 'ouvrage_projet', ['id_projet'])

    # =================================================================
    # 4. TRIGGERS
    # =================================================================
    for table in [
        "source",
        "ref_geo_admin",
        "localite",
        "fichier",
        "ouvrage",
        "cgpe",
        "projet_financement",
    ]:
        op.execute(f"""
            CREATE TRIGGER set_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
        """)

    op.execute("""
        CREATE TRIGGER check_localite_geo
        BEFORE INSERT OR UPDATE OF id_geo ON localite
        FOR EACH ROW EXECUTE FUNCTION trg_check_localite_geo();
    """)

    # =================================================================
    # 5. VUES
    # =================================================================
    op.execute("""
        CREATE OR REPLACE VIEW v_points_par_fichier AS
        SELECT
            f.id_fichier,
            f.nom_fichier_original,
            f.date_ingestion,
            s.nom AS source,
            fe.id_feuille,
            fe.nom_feuille,
            li.id_ligne,
            li.num_ligne_source,
            li.type_ouvrage_brut,
            li.etat_ouvrage_brut,
            li.annee_projet,
            li.bailleur_brut,
            li.type_financement_brut,
            li.statut_qualite,
            li.latitude_decimal,
            li.longitude_decimal,
            li.geom
        FROM ligne_ingeree li
        JOIN feuille fe ON fe.id_feuille = li.id_feuille
        JOIN fichier f  ON f.id_fichier  = fe.id_fichier
        JOIN source s   ON s.id_source   = f.id_source
        WHERE li.geom IS NOT NULL
    """)

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
            g.nom  AS sous_prefecture,
            gp.nom AS departement,
            gr.nom AS region,
            gd.nom AS district,
            o.latitude_decimal,
            o.longitude_decimal,
            o.geom
        FROM ouvrage o
        JOIN localite l        ON l.id_localite = o.id_localite
        JOIN ref_geo_admin g   ON g.id_geo = l.id_geo
        LEFT JOIN ref_geo_admin gp ON gp.id_geo = g.parent_id
        LEFT JOIN ref_geo_admin gr ON gr.id_geo = gp.parent_id
        LEFT JOIN ref_geo_admin gd ON gd.id_geo = gr.parent_id
        WHERE o.geom IS NOT NULL
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_qualite_par_fichier AS
        SELECT
            f.id_fichier,
            f.nom_fichier_original,
            s.nom AS source,
            f.statut,
            f.nb_lignes_total,
            COUNT(*) FILTER (WHERE li.statut_qualite = 'ok')                    AS nb_ok,
            COUNT(*) FILTER (WHERE li.statut_qualite = 'localite_non_resolue')  AS nb_localite_non_resolue,
            COUNT(*) FILTER (WHERE li.statut_qualite = 'geom_invalide')         AS nb_geom_invalide,
            COUNT(*) FILTER (WHERE li.statut_qualite = 'type_ouvrage_inconnu')  AS nb_type_inconnu,
            COUNT(*) FILTER (WHERE li.statut_qualite = 'rejete')                AS nb_rejetes
        FROM fichier f
        JOIN source s ON s.id_source = f.id_source
        LEFT JOIN feuille fe       ON fe.id_fichier = f.id_fichier
        LEFT JOIN ligne_ingeree li ON li.id_feuille = fe.id_feuille
        GROUP BY f.id_fichier, f.nom_fichier_original, s.nom, f.statut, f.nb_lignes_total
    """)

    # =================================================================
    # 6. SEED
    # =================================================================
    op.execute("""
        INSERT INTO source (nom, type_source, commentaire) VALUES
            ('ONEP',   'public',    'Office National de l''Eau Potable'),
            ('SODECI', 'prive',     'Société de Distribution d''Eau de Côte d''Ivoire'),
            ('UNICEF', 'bailleur',  'Fonds des Nations Unies pour l''Enfance'),
            ('BAD',    'bailleur',  'Banque Africaine de Développement'),
            ('LONACI', 'public',    'Loterie Nationale de Côte d''Ivoire'),
            ('ETAT_CI','etat',      'État de Côte d''Ivoire (Ministère de l''Hydraulique)')
        ON CONFLICT (nom) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_qualite_par_fichier")
    op.execute("DROP VIEW IF EXISTS v_points_consolides")
    op.execute("DROP VIEW IF EXISTS v_points_par_fichier")

    op.drop_index('idx_ouvrage_projet_projet', table_name='ouvrage_projet')
    op.drop_table('ouvrage_projet')

    op.drop_index('idx_ligne_geom', table_name='ligne_ingeree', postgresql_using='gist')
    op.drop_index('idx_ligne_type_ouvrage', table_name='ligne_ingeree')
    op.drop_index('idx_ligne_statut_qualite', table_name='ligne_ingeree')
    op.drop_index('idx_ligne_run', table_name='ligne_ingeree')
    op.drop_index('idx_ligne_ouvrage', table_name='ligne_ingeree')
    op.drop_index('idx_ligne_localite', table_name='ligne_ingeree')
    op.drop_index('idx_ligne_feuille', table_name='ligne_ingeree')
    op.drop_index('idx_ligne_donnees_brutes', table_name='ligne_ingeree', postgresql_using='gin')
    op.drop_table('ligne_ingeree')

    op.drop_index('idx_run_statut', table_name='ingestion_run')
    op.drop_index('idx_run_fichier', table_name='ingestion_run')
    op.drop_index('idx_run_feuille', table_name='ingestion_run')
    op.drop_table('ingestion_run')

    op.drop_index('idx_cgpe_ouvrage', table_name='cgpe')
    op.drop_index('idx_cgpe_metadata', table_name='cgpe', postgresql_using='gin')
    op.drop_index('idx_cgpe_localite', table_name='cgpe')
    op.drop_table('cgpe')

    op.drop_index('idx_ouvrage_geom', table_name='ouvrage', postgresql_using='gist')
    op.drop_index('idx_ouvrage_realisation', table_name='ouvrage')
    op.drop_index('idx_ouvrage_alimentation', table_name='ouvrage')
    op.drop_index('idx_ouvrage_nature', table_name='ouvrage')
    op.drop_index('idx_ouvrage_qualite_eau', table_name='ouvrage', postgresql_using='gin')
    op.drop_index('idx_ouvrage_metadata', table_name='ouvrage', postgresql_using='gin')
    op.drop_index('idx_ouvrage_localite', table_name='ouvrage')
    op.drop_index('idx_ouvrage_etat', table_name='ouvrage')
    op.drop_index('idx_ouvrage_code', table_name='ouvrage', postgresql_where='code_ouvrage IS NOT NULL')
    op.drop_table('ouvrage')

    op.drop_index('idx_mapping_feuille_feuille', table_name='mapping_feuille')
    op.drop_table('mapping_feuille')

    op.drop_index('idx_feuille_fichier', table_name='feuille')
    op.drop_table('feuille')

    op.drop_index('idx_projet_source', table_name='projet_financement')
    op.drop_index('idx_projet_annee', table_name='projet_financement')
    op.drop_table('projet_financement')

    op.drop_index('idx_alias_trgm', table_name='localite_alias', postgresql_using='gin')
    op.drop_table('localite_alias')

    op.drop_index('idx_localite_nom_trgm', table_name='localite', postgresql_using='gin')
    op.drop_index('idx_localite_geom', table_name='localite', postgresql_using='gist')
    op.drop_index('idx_localite_metadata', table_name='localite', postgresql_using='gin')
    op.drop_index('idx_localite_geo', table_name='localite')
    op.drop_table('localite')

    op.drop_index('idx_fichier_source', table_name='fichier')
    op.drop_index('idx_fichier_hash', table_name='fichier')
    op.drop_index('idx_fichier_date', table_name='fichier')
    op.drop_table('fichier')

    op.drop_table('source')

    op.drop_index('idx_ref_geo_nom_trgm', table_name='ref_geo_admin', postgresql_using='gin')
    op.drop_index('idx_ref_geo_parent', table_name='ref_geo_admin')
    op.drop_index('idx_ref_geo_niveau', table_name='ref_geo_admin')
    op.drop_table('ref_geo_admin')

    op.execute("DROP FUNCTION IF EXISTS trg_check_localite_geo() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS trg_set_updated_at() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS geom_from_latlon(double precision, double precision) CASCADE")