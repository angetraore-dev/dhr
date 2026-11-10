"""
Modèles SQLAlchemy 2.x — miroir exact de `sql/schema.sql` et de la migration
`0001_initial.py`.

Conventions :
- Colonnes nommées comme en base (snake_case).
- Types PostgreSQL respectés (JSONB, Numeric, DateTime(timezone=True)...).
- Contraintes CHECK et UNIQUE reproduites dans __table_args__.
- Index btree et partiels reproduits dans __table_args__.
- Index GIN/GIST et colonnes générées (`geom`, `geom_centre`) NON déclarés
  en ORM : gérés en migration (SQLAlchemy ne les gère pas nativement).
- `metadata` (colonne) → attribut Python `metadata_` (conflit Base.metadata).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


# =====================================================================
# 1. RÉFÉRENTIELS
# =====================================================================


class Source(Base):
    """Émetteur de fichiers (ONEP, SODECI, UNICEF, BAD, LONACI, ETAT_CI...)."""

    __tablename__ = "source"

    id_source: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    type_source: Mapped[str] = mapped_column(String(30), nullable=False)
    actif: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    commentaire: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "type_source IN ('public','prive','bailleur','etat','autre')",
            name="source_type_source_check",
        ),
        UniqueConstraint("nom", name="uq_source_nom"),
    )

    # Relations
    fichiers: Mapped[list[Fichier]] = relationship(back_populates="source")
    projets_finances: Mapped[list[ProjetFinancement]] = relationship(
        back_populates="financeur"
    )


class RefGeoAdmin(Base):
    """Référentiel administratif hiérarchique auto-référencé."""

    __tablename__ = "ref_geo_admin"

    id_geo: Mapped[int] = mapped_column(Integer, primary_key=True)
    niveau: Mapped[str] = mapped_column(String(20), nullable=False)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ref_geo_admin.id_geo", ondelete="RESTRICT")
    )
    code_officiel: Mapped[str | None] = mapped_column(String(50))
    type_localite: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "niveau IN ('district','region','departement','sous_prefecture','localite')",
            name="ref_geo_admin_niveau_check",
        ),
        CheckConstraint(
            "type_localite IS NULL OR type_localite IN ('village','campement','autre')",
            name="ref_geo_admin_type_localite_check",
        ),
        CheckConstraint(
            "(niveau <> 'localite' AND type_localite IS NULL) OR (niveau = 'localite')",
            name="chk_ref_geo_type_localite",
        ),
        CheckConstraint(
            "(niveau = 'district' AND parent_id IS NULL) "
            "OR (niveau <> 'district' AND parent_id IS NOT NULL)",
            name="chk_ref_geo_parent",
        ),
        UniqueConstraint(
            "parent_id", "nom", "niveau", name="uq_ref_geo_parent_nom_niveau"
        ),
        Index("idx_ref_geo_niveau", "niveau"),
        Index("idx_ref_geo_parent", "parent_id"),
        # idx_ref_geo_nom_trgm : GIN, créé en migration
    )

    parent: Mapped[RefGeoAdmin | None] = relationship(
        remote_side="RefGeoAdmin.id_geo", back_populates="enfants"
    )
    enfants: Mapped[list[RefGeoAdmin]] = relationship(back_populates="parent")
    localites: Mapped[list[Localite]] = relationship(back_populates="ref_geo")


class Localite(Base):
    """Entité métier village/campement rattachée à un nœud niveau='localite'."""

    __tablename__ = "localite"

    id_localite: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_geo: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ref_geo_admin.id_geo", ondelete="RESTRICT"),
        nullable=False,
    )
    nom_usage: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude_centre: Mapped[float | None] = mapped_column(Float)
    longitude_centre: Mapped[float | None] = mapped_column(Float)
    # geom_centre : colonne générée, ajoutée en migration
    commentaire: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_localite_geo", "id_geo"),
        # idx_localite_geom : GIST, créé en migration
        # idx_localite_nom_trgm : GIN, créé en migration
        # idx_localite_metadata : GIN, créé en migration
    )

    ref_geo: Mapped[RefGeoAdmin] = relationship(back_populates="localites")
    alias: Mapped[list[LocaliteAlias]] = relationship(
        back_populates="localite", cascade="all, delete-orphan"
    )
    ouvrages: Mapped[list[Ouvrage]] = relationship(back_populates="localite")
    cgpes: Mapped[list[CGPE]] = relationship(back_populates="localite")
    lignes_ingerees: Mapped[list[LigneIngeree]] = relationship(
        back_populates="localite"
    )


class LocaliteAlias(Base):
    """Variantes de noms d'une localité (V2, vide au MVP)."""

    __tablename__ = "localite_alias"

    id_alias: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_localite: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("localite.id_localite", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(String(150), nullable=False)
    source_alias: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        UniqueConstraint("id_localite", "alias", name="uq_alias_localite"),
        # idx_alias_trgm : GIN, créé en migration
    )

    localite: Mapped[Localite] = relationship(back_populates="alias")


# =====================================================================
# 2. INGESTION
# =====================================================================


class Fichier(Base):
    """Fichier Excel uploadé. hash_sha256 non unique (réingestion légitime)."""

    __tablename__ = "fichier"

    id_fichier: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_source: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("source.id_source", ondelete="RESTRICT"),
        nullable=False,
    )
    nom_fichier_original: Mapped[str] = mapped_column(String(255), nullable=False)
    chemin_stockage: Mapped[str] = mapped_column(Text, nullable=False)
    hash_sha256: Mapped[str | None] = mapped_column(String(64))
    taille_octets: Mapped[int | None] = mapped_column(BigInteger)
    date_reception: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    date_ingestion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'en_attente'")
    )
    nb_feuilles: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    nb_lignes_total: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    est_reingestion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    commentaire: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "statut IN ('en_attente','en_cours','ingere','partiel','erreur')",
            name="fichier_statut_check",
        ),
        Index("idx_fichier_source", "id_source"),
        Index("idx_fichier_date", "date_reception"),
        Index("idx_fichier_hash", "hash_sha256"),
    )

    source: Mapped[Source] = relationship(back_populates="fichiers")
    feuilles: Mapped[list[Feuille]] = relationship(
        back_populates="fichier", cascade="all, delete-orphan"
    )
    runs: Mapped[list[IngestionRun]] = relationship(
        back_populates="fichier", cascade="all, delete-orphan"
    )


class Feuille(Base):
    """Feuille d'un classeur Excel."""

    __tablename__ = "feuille"

    id_feuille: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_fichier: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fichier.id_fichier", ondelete="CASCADE"), nullable=False
    )
    nom_feuille: Mapped[str] = mapped_column(String(150), nullable=False)
    index_feuille: Mapped[int] = mapped_column(Integer, nullable=False)
    type_contenu: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'inconnu'")
    )
    nb_lignes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    nb_lignes_valides: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    statut_ingestion: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'en_attente'")
    )
    message_erreur: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "type_contenu IN ('ouvrages','cgpe','mixte','autre','inconnu')",
            name="feuille_type_contenu_check",
        ),
        CheckConstraint(
            "statut_ingestion IN ('en_attente','en_cours','ingere','partiel','erreur')",
            name="feuille_statut_ingestion_check",
        ),
        UniqueConstraint(
            "id_fichier", "index_feuille", name="uq_feuille_fichier_index"
        ),
        Index("idx_feuille_fichier", "id_fichier"),
    )

    fichier: Mapped[Fichier] = relationship(back_populates="feuilles")
    lignes: Mapped[list[LigneIngeree]] = relationship(
        back_populates="feuille", cascade="all, delete-orphan"
    )
    mappings: Mapped[list[MappingFeuille]] = relationship(
        back_populates="feuille", cascade="all, delete-orphan"
    )
    runs: Mapped[list[IngestionRun]] = relationship(back_populates="feuille")


class MappingFeuille(Base):
    """Mapping validé (entête Excel → champ cible)."""

    __tablename__ = "mapping_feuille"

    id_mapping: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_feuille: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("feuille.id_feuille", ondelete="CASCADE"), nullable=False
    )
    entete_brut: Mapped[str] = mapped_column(String(255), nullable=False)
    champ_cible: Mapped[str | None] = mapped_column(String(100))
    confiance: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    valide_par_utilisateur: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "confiance IS NULL OR (confiance >= 0 AND confiance <= 1)",
            name="mapping_feuille_confiance_check",
        ),
        UniqueConstraint("id_feuille", "entete_brut", name="uq_mapping_feuille_entete"),
        Index("idx_mapping_feuille_feuille", "id_feuille"),
    )

    feuille: Mapped[Feuille] = relationship(back_populates="mappings")


class IngestionRun(Base):
    """Exécution d'ingestion (paramètres + statut)."""

    __tablename__ = "ingestion_run"

    id_run: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_fichier: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fichier.id_fichier", ondelete="CASCADE"), nullable=False
    )
    id_feuille: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("feuille.id_feuille", ondelete="CASCADE")
    )
    mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'complet'")
    )
    limite_lignes: Mapped[int | None] = mapped_column(Integer)
    ligne_debut: Mapped[int | None] = mapped_column(Integer)
    ligne_fin: Mapped[int | None] = mapped_column(Integer)
    nb_lignes_ingerees: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'en_cours'")
    )
    message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "mode IN ('complet','echantillon','plage')",
            name="ingestion_run_mode_check",
        ),
        CheckConstraint(
            "statut IN ('en_cours','termine','erreur','annule')",
            name="ingestion_run_statut_check",
        ),
        CheckConstraint(
            "(mode = 'complet' AND limite_lignes IS NULL AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'echantillon' AND limite_lignes IS NOT NULL AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'plage' AND limite_lignes IS NULL AND ligne_debut IS NOT NULL AND ligne_fin IS NOT NULL "
            "AND ligne_fin >= ligne_debut)",
            name="chk_run_mode_params",
        ),
        Index("idx_run_fichier", "id_fichier"),
        Index("idx_run_feuille", "id_feuille"),
        Index("idx_run_statut", "statut"),
    )

    fichier: Mapped[Fichier] = relationship(back_populates="runs")
    feuille: Mapped[Feuille | None] = relationship(back_populates="runs")
    lignes: Mapped[list[LigneIngeree]] = relationship(back_populates="run")


class LigneIngeree(Base):
    """Ligne brute d'Excel (matière première de la consolidation)."""

    __tablename__ = "ligne_ingeree"

    id_ligne: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_feuille: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("feuille.id_feuille", ondelete="CASCADE"), nullable=False
    )
    id_run: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("ingestion_run.id_run", ondelete="SET NULL")
    )
    num_ligne_source: Mapped[int] = mapped_column(Integer, nullable=False)
    donnees_brutes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Contexte administratif
    district_brut: Mapped[str | None] = mapped_column(String(150))
    region_brute: Mapped[str | None] = mapped_column(String(150))
    departement_brut: Mapped[str | None] = mapped_column(String(150))
    sous_prefecture_brute: Mapped[str | None] = mapped_column(String(150))
    localite_brute: Mapped[str | None] = mapped_column(String(150))
    type_localite_brut: Mapped[str | None] = mapped_column(String(30))

    # Coordonnées
    latitude_decimal: Mapped[float | None] = mapped_column(Float)
    longitude_decimal: Mapped[float | None] = mapped_column(Float)
    # geom : colonne générée, ajoutée en migration

    # Attributs métier bruts (P12)
    type_ouvrage_brut: Mapped[str | None] = mapped_column(String(50))
    etat_ouvrage_brut: Mapped[str | None] = mapped_column(String(50))
    annee_projet: Mapped[int | None] = mapped_column(Integer)
    bailleur_brut: Mapped[str | None] = mapped_column(String(150))
    type_financement_brut: Mapped[str | None] = mapped_column(String(50))
    usage_ouvrage_brut: Mapped[str | None] = mapped_column(String(50))
    a_cgpe: Mapped[bool | None] = mapped_column(Boolean)

    # Qualité
    statut_qualite: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'ok'")
    )
    message_qualite: Mapped[str | None] = mapped_column(Text)
    id_localite: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("localite.id_localite", ondelete="SET NULL")
    )
    id_ouvrage_consolide: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("ouvrage.id_ouvrage", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "statut_qualite IN ('ok','localite_non_resolue','geom_invalide',"
            "'type_ouvrage_inconnu','rejete','doublon_suspect')",
            name="ligne_ingeree_statut_qualite_check",
        ),
        UniqueConstraint(
            "id_feuille", "id_run", "num_ligne_source", name="uq_ligne_feuille_run_num"
        ),
        Index("idx_ligne_feuille", "id_feuille"),
        Index("idx_ligne_run", "id_run"),
        # idx_ligne_geom : GIST, créé en migration
        Index("idx_ligne_statut_qualite", "statut_qualite"),
        Index("idx_ligne_localite", "id_localite"),
        Index("idx_ligne_type_ouvrage", "type_ouvrage_brut"),
        Index("idx_ligne_usage_ouvrage", "usage_ouvrage_brut"),
        # idx_ligne_donnees_brutes : GIN, créé en migration
        Index("idx_ligne_ouvrage", "id_ouvrage_consolide"),
    )

    feuille: Mapped[Feuille] = relationship(back_populates="lignes")
    run: Mapped[IngestionRun | None] = relationship(back_populates="lignes")
    localite: Mapped[Localite | None] = relationship(back_populates="lignes_ingerees")
    ouvrage_consolide: Mapped[Ouvrage | None] = relationship(
        back_populates="lignes_sources"
    )


# =====================================================================
# 3. MÉTIER CONSOLIDÉ
# =====================================================================


class Ouvrage(Base):
    """Ouvrage consolidé (dédoublonné)."""

    __tablename__ = "ouvrage"

    id_ouvrage: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code_ouvrage: Mapped[str | None] = mapped_column(String(100))
    id_localite: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("localite.id_localite", ondelete="RESTRICT"),
        nullable=False,
    )
    nature_ouvrage: Mapped[str | None] = mapped_column(String(20))
    type_alimentation: Mapped[str | None] = mapped_column(String(20))
    realisation_par: Mapped[str | None] = mapped_column(String(20))
    etat: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'inconnu'")
    )
    annee_realisation: Mapped[int | None] = mapped_column(Integer)
    latitude_decimal: Mapped[float | None] = mapped_column(Float)
    longitude_decimal: Mapped[float | None] = mapped_column(Float)
    # geom : colonne générée, ajoutée en migration
    commentaire: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    qualite_eau: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "nature_ouvrage IS NULL OR nature_ouvrage IN ('puits','forage','inconnu')",
            name="ouvrage_nature_check",
        ),
        CheckConstraint(
            "type_alimentation IS NULL OR type_alimentation IN ('PMH','HVA','PEA','HV','AUTRE')",
            name="ouvrage_alimentation_check",
        ),
        CheckConstraint(
            "realisation_par IS NULL OR realisation_par IN ('public','prive','inconnu')",
            name="ouvrage_realisation_check",
        ),
        CheckConstraint(
            "etat IN ('fonctionnel','en_panne','abandonne','inconnu')",
            name="ouvrage_etat_check",
        ),
        Index(
            "idx_ouvrage_code",
            "code_ouvrage",
            postgresql_where=text("code_ouvrage IS NOT NULL"),
        ),
        Index("idx_ouvrage_localite", "id_localite"),
        Index("idx_ouvrage_etat", "etat"),
        Index("idx_ouvrage_nature", "nature_ouvrage"),
        Index("idx_ouvrage_alimentation", "type_alimentation"),
        Index("idx_ouvrage_realisation", "realisation_par"),
        # idx_ouvrage_geom : GIST, créé en migration
        # idx_ouvrage_metadata, idx_ouvrage_qualite_eau : GIN, créés en migration
    )

    localite: Mapped[Localite] = relationship(back_populates="ouvrages")
    cgpes: Mapped[list[CGPE]] = relationship(back_populates="ouvrage")
    financements: Mapped[list[OuvrageProjet]] = relationship(
        back_populates="ouvrage", cascade="all, delete-orphan"
    )
    lignes_sources: Mapped[list[LigneIngeree]] = relationship(
        back_populates="ouvrage_consolide"
    )


class CGPE(Base):
    """Comité de Gestion de Point d'Eau (V2, vide au MVP)."""

    __tablename__ = "cgpe"

    id_cgpe: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_localite: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("localite.id_localite", ondelete="CASCADE"),
        nullable=False,
    )
    id_ouvrage: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("ouvrage.id_ouvrage", ondelete="SET NULL")
    )
    existe: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    date_creation: Mapped[date | None] = mapped_column(Date)
    statut: Mapped[str | None] = mapped_column(String(20))
    nb_membres: Mapped[int | None] = mapped_column(Integer)
    commentaire: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "statut IS NULL OR statut IN ('fonctionnel','non_fonctionnel','inconnu')",
            name="cgpe_statut_check",
        ),
        Index("idx_cgpe_localite", "id_localite"),
        Index("idx_cgpe_ouvrage", "id_ouvrage"),
        # idx_cgpe_metadata : GIN, créé en migration
    )

    localite: Mapped[Localite] = relationship(back_populates="cgpes")
    ouvrage: Mapped[Ouvrage | None] = relationship(back_populates="cgpes")


class ProjetFinancement(Base):
    """Projet de financement porté par un bailleur ou l'État (V2, vide au MVP)."""

    __tablename__ = "projet_financement"

    id_projet: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom_projet: Mapped[str] = mapped_column(String(255), nullable=False)
    annee: Mapped[int | None] = mapped_column(Integer)
    id_source_financeur: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("source.id_source", ondelete="RESTRICT"),
        nullable=False,
    )
    type_financement: Mapped[str] = mapped_column(String(20), nullable=False)
    montant: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    devise: Mapped[str | None] = mapped_column(String(3), server_default=text("'XOF'"))
    commentaire: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "type_financement IN ('etat','prive','partenariat','inconnu')",
            name="projet_financement_type_check",
        ),
        Index("idx_projet_annee", "annee"),
        Index("idx_projet_source", "id_source_financeur"),
    )

    financeur: Mapped[Source] = relationship(back_populates="projets_finances")
    ouvrages: Mapped[list[OuvrageProjet]] = relationship(
        back_populates="projet", cascade="all, delete-orphan"
    )


class OuvrageProjet(Base):
    """Association N..N Ouvrage ↔ Projet avec rôle (V2, vide au MVP)."""

    __tablename__ = "ouvrage_projet"

    id_ouvrage: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ouvrage.id_ouvrage", ondelete="CASCADE"),
        primary_key=True,
    )
    id_projet: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projet_financement.id_projet", ondelete="CASCADE"),
        primary_key=True,
    )
    role_financement: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'principal'")
    )

    __table_args__ = (
        CheckConstraint(
            "role_financement IN ('principal','co_financement')",
            name="ouvrage_projet_role_check",
        ),
        Index("idx_ouvrage_projet_projet", "id_projet"),
    )

    ouvrage: Mapped[Ouvrage] = relationship(back_populates="financements")
    projet: Mapped[ProjetFinancement] = relationship(back_populates="ouvrages")