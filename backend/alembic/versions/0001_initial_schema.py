"""0001_initial

Migration initiale unique du projet DHR. Reproduit à l'identique
`sql/schema.sql` (extensions, fonctions, tables, index, triggers, vues, seed).

Revision ID: 0001_initial
Revises: (aucune — c'est la première)
Create Date: 2026-11-10

Point de non-retour : une fois cette migration appliquée et la base recréée,
on ne revient pas aux anciennes migrations. Voir Bible § 2.1.6 et ADR-018.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# =====================================================================
# UPGRADE
# =====================================================================
def upgrade() -> None:
    # -----------------------------------------------------------------
    # 1. EXTENSIONS
    # -----------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")

    # -----------------------------------------------------------------
    # 2. FONCTIONS
    # -----------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION geom_from_latlon(
            lat double precision,
            lon double precision
        ) RETURNS geometry(Point, 4326)
        LANGUAGE plpgsql
        IMMUTABLE STRICT
        AS $$
        BEGIN
            IF lat IS NULL OR lon IS NULL THEN
                RETURN NULL;
            END IF;
            IF lat < -90 OR lat > 90 OR lon < -180 OR lon > 180 THEN
                RETURN NULL;
            END IF;
            IF lat = 0 AND lon = 0 THEN
                RETURN NULL;
            END IF;
            RETURN ST_SetSRID(ST_MakePoint(lon, lat), 4326);
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_set_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_check_localite_geo()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_niveau varchar(20);
        BEGIN
            SELECT niveau INTO v_niveau
            FROM ref_geo_admin
            WHERE id_geo = NEW.id_geo;

            IF v_niveau IS NULL THEN
                RAISE EXCEPTION 'ref_geo_admin.id_geo=% introuvable', NEW.id_geo;
            END IF;
            IF v_niveau != 'localite' THEN
                RAISE EXCEPTION 'localite.id_geo=% doit pointer vers un nœud de niveau ''localite'' (trouvé: %)',
                    NEW.id_geo, v_niveau;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )

    # -----------------------------------------------------------------
    # 3. TABLES — GROUPE A : RÉFÉRENTIELS
    # -----------------------------------------------------------------
    op.create_table(
        "source",
        sa.Column("id_source", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.Column("type_source", sa.String(length=30), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "type_source IN ('public','prive','bailleur','etat','autre')",
            name="source_type_source_check",
        ),
        sa.UniqueConstraint("nom", name="uq_source_nom"),
    )

    op.create_table(
        "ref_geo_admin",
        sa.Column("id_geo", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("niveau", sa.String(length=20), nullable=False),
        sa.Column("nom", sa.String(length=150), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("code_officiel", sa.String(length=50), nullable=True),
        sa.Column("type_localite", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "niveau IN ('district','region','departement','sous_prefecture','localite')",
            name="ref_geo_admin_niveau_check",
        ),
        sa.CheckConstraint(
            "type_localite IS NULL OR type_localite IN ('village','campement','autre')",
            name="ref_geo_admin_type_localite_check",
        ),
        sa.CheckConstraint(
            "(niveau <> 'localite' AND type_localite IS NULL) OR (niveau = 'localite')",
            name="chk_ref_geo_type_localite",
        ),
        sa.CheckConstraint(
            "(niveau = 'district' AND parent_id IS NULL) "
            "OR (niveau <> 'district' AND parent_id IS NOT NULL)",
            name="chk_ref_geo_parent",
        ),
        sa.UniqueConstraint("parent_id", "nom", "niveau", name="uq_ref_geo_parent_nom_niveau"),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["ref_geo_admin.id_geo"],
            name="ref_geo_admin_parent_id_fkey", ondelete="RESTRICT",
        ),
    )
    op.create_index("idx_ref_geo_niveau", "ref_geo_admin", ["niveau"])
    op.create_index("idx_ref_geo_parent", "ref_geo_admin", ["parent_id"])
    op.execute(
        "CREATE INDEX idx_ref_geo_nom_trgm ON ref_geo_admin USING gin (nom gin_trgm_ops)"
    )

    op.create_table(
        "localite",
        sa.Column("id_localite", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_geo", sa.Integer(), nullable=False),
        sa.Column("nom_usage", sa.String(length=150), nullable=False),
        sa.Column("latitude_centre", sa.Float(), nullable=True),
        sa.Column("longitude_centre", sa.Float(), nullable=True),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # geom_centre : colonne générée, ajoutée en SQL brut après create_table
        sa.ForeignKeyConstraint(
            ["id_geo"], ["ref_geo_admin.id_geo"],
            name="localite_id_geo_fkey", ondelete="RESTRICT",
        ),
    )
    op.execute(
        "ALTER TABLE localite ADD COLUMN geom_centre geometry(Point, 4326) "
        "GENERATED ALWAYS AS (geom_from_latlon(latitude_centre, longitude_centre)) STORED"
    )
    op.create_index("idx_localite_geo", "localite", ["id_geo"])
    op.execute("CREATE INDEX idx_localite_geom ON localite USING gist (geom_centre)")
    op.execute("CREATE INDEX idx_localite_nom_trgm ON localite USING gin (nom_usage gin_trgm_ops)")
    op.execute("CREATE INDEX idx_localite_metadata ON localite USING gin (metadata)")

    op.create_table(
        "localite_alias",
        sa.Column("id_alias", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_localite", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=150), nullable=False),
        sa.Column("source_alias", sa.String(length=100), nullable=True),
        sa.UniqueConstraint("id_localite", "alias", name="uq_alias_localite"),
        sa.ForeignKeyConstraint(
            ["id_localite"], ["localite.id_localite"],
            name="localite_alias_id_localite_fkey", ondelete="CASCADE",
        ),
    )
    op.execute("CREATE INDEX idx_alias_trgm ON localite_alias USING gin (alias gin_trgm_ops)")

    # -----------------------------------------------------------------
    # 4. TABLES — GROUPE B : INGESTION
    # -----------------------------------------------------------------
    op.create_table(
        "fichier",
        sa.Column("id_fichier", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("id_source", sa.Integer(), nullable=False),
        sa.Column("nom_fichier_original", sa.String(length=255), nullable=False),
        sa.Column("chemin_stockage", sa.Text(), nullable=False),
        sa.Column("hash_sha256", sa.String(length=64), nullable=True),
        sa.Column("taille_octets", sa.BigInteger(), nullable=True),
        sa.Column("date_reception", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("date_ingestion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("statut", sa.String(length=20), nullable=False, server_default=sa.text("'en_attente'")),
        sa.Column("nb_feuilles", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("nb_lignes_total", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("est_reingestion", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "statut IN ('en_attente','en_cours','ingere','partiel','erreur')",
            name="fichier_statut_check",
        ),
        sa.ForeignKeyConstraint(
            ["id_source"], ["source.id_source"],
            name="fichier_id_source_fkey", ondelete="RESTRICT",
        ),
    )
    op.create_index("idx_fichier_source", "fichier", ["id_source"])
    op.create_index("idx_fichier_date", "fichier", ["date_reception"])
    op.create_index("idx_fichier_hash", "fichier", ["hash_sha256"])

    op.create_table(
        "feuille",
        sa.Column("id_feuille", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("id_fichier", sa.BigInteger(), nullable=False),
        sa.Column("nom_feuille", sa.String(length=150), nullable=False),
        sa.Column("index_feuille", sa.Integer(), nullable=False),
        sa.Column("type_contenu", sa.String(length=20), nullable=False, server_default=sa.text("'inconnu'")),
        sa.Column("nb_lignes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("nb_lignes_valides", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("statut_ingestion", sa.String(length=20), nullable=False, server_default=sa.text("'en_attente'")),
        sa.Column("message_erreur", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "type_contenu IN ('ouvrages','cgpe','mixte','autre','inconnu')",
            name="feuille_type_contenu_check",
        ),
        sa.CheckConstraint(
            "statut_ingestion IN ('en_attente','en_cours','ingere','partiel','erreur')",
            name="feuille_statut_ingestion_check",
        ),
        sa.UniqueConstraint("id_fichier", "index_feuille", name="uq_feuille_fichier_index"),
        sa.ForeignKeyConstraint(
            ["id_fichier"], ["fichier.id_fichier"],
            name="feuille_id_fichier_fkey", ondelete="CASCADE",
        ),
    )
    op.create_index("idx_feuille_fichier", "feuille", ["id_fichier"])

    op.create_table(
        "mapping_feuille",
        sa.Column("id_mapping", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_feuille", sa.BigInteger(), nullable=False),
        sa.Column("entete_brut", sa.String(length=255), nullable=False),
        sa.Column("champ_cible", sa.String(length=100), nullable=True),
        sa.Column("confiance", sa.Numeric(3, 2), nullable=True),
        sa.Column("valide_par_utilisateur", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "confiance IS NULL OR (confiance >= 0 AND confiance <= 1)",
            name="mapping_feuille_confiance_check",
        ),
        sa.UniqueConstraint("id_feuille", "entete_brut", name="uq_mapping_feuille_entete"),
        sa.ForeignKeyConstraint(
            ["id_feuille"], ["feuille.id_feuille"],
            name="mapping_feuille_id_feuille_fkey", ondelete="CASCADE",
        ),
    )
    op.create_index("idx_mapping_feuille_feuille", "mapping_feuille", ["id_feuille"])

    op.create_table(
        "ingestion_run",
        sa.Column("id_run", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("id_fichier", sa.BigInteger(), nullable=False),
        sa.Column("id_feuille", sa.BigInteger(), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=False, server_default=sa.text("'complet'")),
        sa.Column("limite_lignes", sa.Integer(), nullable=True),
        sa.Column("ligne_debut", sa.Integer(), nullable=True),
        sa.Column("ligne_fin", sa.Integer(), nullable=True),
        sa.Column("nb_lignes_ingerees", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("statut", sa.String(length=20), nullable=False, server_default=sa.text("'en_cours'")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "mode IN ('complet','echantillon','plage')",
            name="ingestion_run_mode_check",
        ),
        sa.CheckConstraint(
            "statut IN ('en_cours','termine','erreur','annule')",
            name="ingestion_run_statut_check",
        ),
        sa.CheckConstraint(
            "(mode = 'complet' AND limite_lignes IS NULL AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'echantillon' AND limite_lignes IS NOT NULL AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'plage' AND limite_lignes IS NULL AND ligne_debut IS NOT NULL AND ligne_fin IS NOT NULL "
            "AND ligne_fin >= ligne_debut)",
            name="chk_run_mode_params",
        ),
        sa.ForeignKeyConstraint(
            ["id_fichier"], ["fichier.id_fichier"],
            name="ingestion_run_id_fichier_fkey", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_feuille"], ["feuille.id_feuille"],
            name="ingestion_run_id_feuille_fkey", ondelete="CASCADE",
        ),
    )
    op.create_index("idx_run_fichier", "ingestion_run", ["id_fichier"])
    op.create_index("idx_run_feuille", "ingestion_run", ["id_feuille"])
    op.create_index("idx_run_statut", "ingestion_run", ["statut"])

    # NOTE : ligne_ingeree est créée APRÈS ouvrage (pour la FK id_ouvrage_consolide).
    # On la crée ici mais sans la FK, puis on ajoute la FK après ouvrage.

    op.create_table(
        "ligne_ingeree",
        sa.Column("id_ligne", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("id_feuille", sa.BigInteger(), nullable=False),
        sa.Column("id_run", sa.BigInteger(), nullable=True),
        sa.Column("num_ligne_source", sa.Integer(), nullable=False),
        sa.Column("donnees_brutes", postgresql.JSONB(), nullable=False),
        sa.Column("district_brut", sa.String(length=150), nullable=True),
        sa.Column("region_brute", sa.String(length=150), nullable=True),
        sa.Column("departement_brut", sa.String(length=150), nullable=True),
        sa.Column("sous_prefecture_brute", sa.String(length=150), nullable=True),
        sa.Column("localite_brute", sa.String(length=150), nullable=True),
        sa.Column("type_localite_brut", sa.String(length=30), nullable=True),
        sa.Column("latitude_decimal", sa.Float(), nullable=True),
        sa.Column("longitude_decimal", sa.Float(), nullable=True),
        sa.Column("type_ouvrage_brut", sa.String(length=50), nullable=True),
        sa.Column("etat_ouvrage_brut", sa.String(length=50), nullable=True),
        sa.Column("annee_projet", sa.Integer(), nullable=True),
        sa.Column("bailleur_brut", sa.String(length=150), nullable=True),
        sa.Column("type_financement_brut", sa.String(length=50), nullable=True),
        sa.Column("usage_ouvrage_brut", sa.String(length=50), nullable=True),
        sa.Column("a_cgpe", sa.Boolean(), nullable=True),
        sa.Column("statut_qualite", sa.String(length=30), nullable=False, server_default=sa.text("'ok'")),
        sa.Column("message_qualite", sa.Text(), nullable=True),
        sa.Column("id_localite", sa.Integer(), nullable=True),
        sa.Column("id_ouvrage_consolide", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # geom : colonne générée, ajoutée en SQL brut
        sa.CheckConstraint(
            "statut_qualite IN ('ok','localite_non_resolue','geom_invalide',"
            "'type_ouvrage_inconnu','rejete','doublon_suspect')",
            name="ligne_ingeree_statut_qualite_check",
        ),
        sa.UniqueConstraint("id_feuille", "id_run", "num_ligne_source", name="uq_ligne_feuille_run_num"),
        sa.ForeignKeyConstraint(
            ["id_feuille"], ["feuille.id_feuille"],
            name="ligne_ingeree_id_feuille_fkey", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_run"], ["ingestion_run.id_run"],
            name="ligne_ingeree_id_run_fkey", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["id_localite"], ["localite.id_localite"],
            name="ligne_ingeree_id_localite_fkey", ondelete="SET NULL",
        ),
        # FK id_ouvrage_consolide ajoutée après ouvrage
    )
    op.execute(
        "ALTER TABLE ligne_ingeree ADD COLUMN geom geometry(Point, 4326) "
        "GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED"
    )
    op.create_index("idx_ligne_feuille", "ligne_ingeree", ["id_feuille"])
    op.create_index("idx_ligne_run", "ligne_ingeree", ["id_run"])
    op.execute("CREATE INDEX idx_ligne_geom ON ligne_ingeree USING gist (geom)")
    op.create_index("idx_ligne_statut_qualite", "ligne_ingeree", ["statut_qualite"])
    op.create_index("idx_ligne_localite", "ligne_ingeree", ["id_localite"])
    op.create_index("idx_ligne_type_ouvrage", "ligne_ingeree", ["type_ouvrage_brut"])
    op.create_index("idx_ligne_usage_ouvrage", "ligne_ingeree", ["usage_ouvrage_brut"])
    op.execute("CREATE INDEX idx_ligne_donnees_brutes ON ligne_ingeree USING gin (donnees_brutes)")
    op.create_index("idx_ligne_ouvrage", "ligne_ingeree", ["id_ouvrage_consolide"])

    # -----------------------------------------------------------------
    # 5. TABLES — GROUPE C : MÉTIER CONSOLIDÉ
    # -----------------------------------------------------------------
    op.create_table(
        "ouvrage",
        sa.Column("id_ouvrage", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code_ouvrage", sa.String(length=100), nullable=True),
        sa.Column("id_localite", sa.Integer(), nullable=False),
        sa.Column("nature_ouvrage", sa.String(length=20), nullable=True),
        sa.Column("type_alimentation", sa.String(length=20), nullable=True),
        sa.Column("realisation_par", sa.String(length=20), nullable=True),
        sa.Column("etat", sa.String(length=20), nullable=False, server_default=sa.text("'inconnu'")),
        sa.Column("annee_realisation", sa.Integer(), nullable=True),
        sa.Column("latitude_decimal", sa.Float(), nullable=True),
        sa.Column("longitude_decimal", sa.Float(), nullable=True),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("qualite_eau", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # geom : colonne générée
        sa.CheckConstraint(
            "nature_ouvrage IS NULL OR nature_ouvrage IN ('puits','forage','inconnu')",
            name="ouvrage_nature_check",
        ),
        sa.CheckConstraint(
            "type_alimentation IS NULL OR type_alimentation IN ('PMH','HVA','PEA','HV','AUTRE')",
            name="ouvrage_alimentation_check",
        ),
        sa.CheckConstraint(
            "realisation_par IS NULL OR realisation_par IN ('public','prive','inconnu')",
            name="ouvrage_realisation_check",
        ),
        sa.CheckConstraint(
            "etat IN ('fonctionnel','en_panne','abandonne','inconnu')",
            name="ouvrage_etat_check",
        ),
        sa.ForeignKeyConstraint(
            ["id_localite"], ["localite.id_localite"],
            name="ouvrage_id_localite_fkey", ondelete="RESTRICT",
        ),
    )
    op.execute(
        "ALTER TABLE ouvrage ADD COLUMN geom geometry(Point, 4326) "
        "GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED"
    )
    op.create_index(
        "idx_ouvrage_code", "ouvrage", ["code_ouvrage"],
        postgresql_where=sa.text("code_ouvrage IS NOT NULL"),
    )
    op.create_index("idx_ouvrage_localite", "ouvrage", ["id_localite"])
    op.create_index("idx_ouvrage_etat", "ouvrage", ["etat"])
    op.create_index("idx_ouvrage_nature", "ouvrage", ["nature_ouvrage"])
    op.create_index("idx_ouvrage_alimentation", "ouvrage", ["type_alimentation"])
    op.create_index("idx_ouvrage_realisation", "ouvrage", ["realisation_par"])
    op.execute("CREATE INDEX idx_ouvrage_geom ON ouvrage USING gist (geom)")
    op.execute("CREATE INDEX idx_ouvrage_metadata ON ouvrage USING gin (metadata)")
    op.execute("CREATE INDEX idx_ouvrage_qualite_eau ON ouvrage USING gin (qualite_eau)")

    # Ajout de la FK ligne_ingeree.id_ouvrage_consolide (ouvrage existe maintenant)
    op.create_foreign_key(
        "ligne_ingeree_id_ouvrage_consolide_fkey",
        "ligne_ingeree", "ouvrage",
        ["id_ouvrage_consolide"], ["id_ouvrage"],
        ondelete="SET NULL",
    )

    op.create_table(
        "cgpe",
        sa.Column("id_cgpe", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_localite", sa.Integer(), nullable=False),
        sa.Column("id_ouvrage", sa.BigInteger(), nullable=True),
        sa.Column("existe", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("date_creation", sa.Date(), nullable=True),
        sa.Column("statut", sa.String(length=20), nullable=True),
        sa.Column("nb_membres", sa.Integer(), nullable=True),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "statut IS NULL OR statut IN ('fonctionnel','non_fonctionnel','inconnu')",
            name="cgpe_statut_check",
        ),
        sa.ForeignKeyConstraint(
            ["id_localite"], ["localite.id_localite"],
            name="cgpe_id_localite_fkey", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_ouvrage"], ["ouvrage.id_ouvrage"],
            name="cgpe_id_ouvrage_fkey", ondelete="SET NULL",
        ),
    )
    op.create_index("idx_cgpe_localite", "cgpe", ["id_localite"])
    op.create_index("idx_cgpe_ouvrage", "cgpe", ["id_ouvrage"])
    op.execute("CREATE INDEX idx_cgpe_metadata ON cgpe USING gin (metadata)")

    op.create_table(
        "projet_financement",
        sa.Column("id_projet", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("nom_projet", sa.String(length=255), nullable=False),
        sa.Column("annee", sa.Integer(), nullable=True),
        sa.Column("id_source_financeur", sa.Integer(), nullable=False),
        sa.Column("type_financement", sa.String(length=20), nullable=False),
        sa.Column("montant", sa.Numeric(18, 2), nullable=True),
        sa.Column("devise", sa.String(length=3), server_default=sa.text("'XOF'")),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "type_financement IN ('etat','prive','partenariat','inconnu')",
            name="projet_financement_type_check",
        ),
        sa.ForeignKeyConstraint(
            ["id_source_financeur"], ["source.id_source"],
            name="projet_financement_id_source_financeur_fkey", ondelete="RESTRICT",
        ),
    )
    op.create_index("idx_projet_annee", "projet_financement", ["annee"])
    op.create_index("idx_projet_source", "projet_financement", ["id_source_financeur"])

    op.create_table(
        "ouvrage_projet",
        sa.Column("id_ouvrage", sa.BigInteger(), nullable=False),
        sa.Column("id_projet", sa.BigInteger(), nullable=False),
        sa.Column("role_financement", sa.String(length=20), nullable=False, server_default=sa.text("'principal'")),
        sa.PrimaryKeyConstraint("id_ouvrage", "id_projet"),
        sa.CheckConstraint(
            "role_financement IN ('principal','co_financement')",
            name="ouvrage_projet_role_check",
        ),
        sa.ForeignKeyConstraint(
            ["id_ouvrage"], ["ouvrage.id_ouvrage"],
            name="ouvrage_projet_id_ouvrage_fkey", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_projet"], ["projet_financement.id_projet"],
            name="ouvrage_projet_id_projet_fkey", ondelete="CASCADE",
        ),
    )
    op.create_index("idx_ouvrage_projet_projet", "ouvrage_projet", ["id_projet"])

    # -----------------------------------------------------------------
    # 6. TRIGGERS
    # -----------------------------------------------------------------
    for table in (
        "source", "ref_geo_admin", "localite", "fichier",
        "ouvrage", "cgpe", "projet_financement",
    ):
        op.execute(
            f"CREATE TRIGGER set_updated_at BEFORE UPDATE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at()"
        )

    op.execute(
        "CREATE TRIGGER check_localite_geo BEFORE INSERT OR UPDATE OF id_geo ON localite "
        "FOR EACH ROW EXECUTE FUNCTION trg_check_localite_geo()"
    )

    # -----------------------------------------------------------------
    # 7. VUES
    # -----------------------------------------------------------------
    op.execute(
        """
        CREATE VIEW v_points_par_fichier AS
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
        JOIN fichier f ON f.id_fichier = fe.id_fichier
        JOIN source s ON s.id_source = f.id_source
        WHERE li.geom IS NOT NULL
          AND NOT (
              unaccent(lower(fe.nom_feuille)) LIKE '%localite%'
           OR unaccent(lower(fe.nom_feuille)) LIKE '%village%'
           OR unaccent(lower(fe.nom_feuille)) LIKE '%campement%'
          )
        """
    )

    op.execute(
        """
        CREATE VIEW v_points_consolides AS
        SELECT
            o.id_ouvrage,
            o.code_ouvrage,
            o.etat,
            o.nature_ouvrage,
            o.type_alimentation,
            o.realisation_par,
            o.annee_realisation,
            l.nom_usage AS localite,
            gp.nom AS sous_prefecture,
            gr.nom AS departement,
            gd.nom AS region,
            o.latitude_decimal,
            o.longitude_decimal,
            o.geom,
            o.metadata,
            o.qualite_eau
        FROM ouvrage o
        JOIN localite l ON l.id_localite = o.id_localite
        JOIN ref_geo_admin g ON g.id_geo = l.id_geo
        LEFT JOIN ref_geo_admin gp ON gp.id_geo = g.parent_id
        LEFT JOIN ref_geo_admin gr ON gr.id_geo = gp.parent_id
        LEFT JOIN ref_geo_admin gd ON gd.id_geo = gr.parent_id
        WHERE o.geom IS NOT NULL
        """
    )

    op.execute(
        """
        CREATE VIEW v_qualite_par_fichier AS
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
            COUNT(*) FILTER (WHERE li.statut_qualite = 'doublon_suspect')       AS nb_doublon_suspect,
            (f.nb_lignes_total - COUNT(li.id_ligne))                            AS nb_rejetes
        FROM fichier f
        JOIN source s ON s.id_source = f.id_source
        LEFT JOIN feuille fe ON fe.id_fichier = f.id_fichier
        LEFT JOIN ligne_ingeree li ON li.id_feuille = fe.id_feuille
        GROUP BY f.id_fichier, f.nom_fichier_original, s.nom, f.statut, f.nb_lignes_total
        """
    )

    # -----------------------------------------------------------------
    # 8. SEED — Sources
    # -----------------------------------------------------------------
    op.execute(
        """
        INSERT INTO source (nom, type_source) VALUES
            ('ONEP',    'public'),
            ('SODECI',  'prive'),
            ('UNICEF',  'bailleur'),
            ('BAD',     'bailleur'),
            ('LONACI',  'public'),
            ('ETAT_CI', 'etat')
        ON CONFLICT (nom) DO NOTHING
        """
    )


# =====================================================================
# DOWNGRADE
# =====================================================================
def downgrade() -> None:
    # Vues
    op.execute("DROP VIEW IF EXISTS v_qualite_par_fichier")
    op.execute("DROP VIEW IF EXISTS v_points_consolides")
    op.execute("DROP VIEW IF EXISTS v_points_par_fichier")

    # Triggers (drop automatique avec les tables, mais on explicite pour clarté)
    for table in (
        "projet_financement", "cgpe", "ouvrage", "fichier",
        "localite", "ref_geo_admin", "source",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS set_updated_at ON {table}")
    op.execute("DROP TRIGGER IF EXISTS check_localite_geo ON localite")

    # Tables (ordre inverse des dépendances)
    op.drop_table("ouvrage_projet")
    op.drop_table("projet_financement")
    op.drop_table("cgpe")
    op.drop_table("ouvrage")
    op.drop_table("ligne_ingeree")
    op.drop_table("ingestion_run")
    op.drop_table("mapping_feuille")
    op.drop_table("feuille")
    op.drop_table("fichier")
    op.drop_table("localite_alias")
    op.drop_table("localite")
    op.drop_table("ref_geo_admin")
    op.drop_table("source")

    # Fonctions
    op.execute("DROP FUNCTION IF EXISTS trg_check_localite_geo()")
    op.execute("DROP FUNCTION IF EXISTS trg_set_updated_at()")
    op.execute("DROP FUNCTION IF EXISTS geom_from_latlon(double precision, double precision)")

    # Extensions (NE PAS supprimer : partagées avec d'autres schémas potentiels)
    # On ne fait rien : les extensions restent installées.