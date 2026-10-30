"""
Modèles SQLAlchemy 2.x + GeoAlchemy2 — miroir exact de sql/schema.sql.

Conventions :
- DeclarativeBase commune (app.db.Base)
- Colonnes nommées comme en base (snake_case)
- Types PostgreSQL respectés (jsonb, geometry, timestamptz…)
- Contraintes CHECK reproduites via CheckConstraint
- Index reproduits via Index (dans __table_args__)
- Colonnes générées (geom) : NON déclarées en ORM, ajoutées en migration manuelle
  (SQLAlchemy ne gère pas GENERATED ALWAYS AS ... STORED de façon portable)

Sections :
1. Référentiels
2. Ingestion
3. Métier consolidé
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
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
# Helpers de typage
# =====================================================================

# On utilise BigInteger pour les PK/FK "bigserial", Integer pour "serial".
# Pour les timestamptz, DateTime(timezone=True).
# Pour les jsonb, JSONB (dialecte PostgreSQL).


# =====================================================================
# 1. RÉFÉRENTIELS
# =====================================================================


class Source(Base):
    """Émetteur de fichiers : structure publique, privée, bailleur, État."""

    __tablename__ = "source"

    id_source: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type_source: Mapped[str] = mapped_column(String(30), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
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
    )

    # Relations
    fichiers: Mapped[list[Fichier]] = relationship(back_populates="source")
    projets_finances: Mapped[list[ProjetFinancement]] = relationship(back_populates="financeur")


class TypeOuvrage(Base):
    """Nomenclature contrôlée : PMH, HV, HVA, PEA, AUTRE."""

    __tablename__ = "type_ouvrage"

    id_type_ouvrage: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    libelle: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    ouvrages: Mapped[list[Ouvrage]] = relationship(back_populates="type_ouvrage")


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
            "(niveau <> 'localite' AND type_localite IS NULL) "
            "OR (niveau = 'localite')",
            name="chk_ref_geo_type_localite",
        ),
        CheckConstraint(
            "(niveau = 'district' AND parent_id IS NULL) "
            "OR (niveau <> 'district' AND parent_id IS NOT NULL)",
            name="chk_ref_geo_parent",
        ),
        UniqueConstraint("parent_id", "nom", "niveau", name="uq_ref_geo_parent_nom_niveau"),
        Index("idx_ref_geo_parent", "parent_id"),
        Index("idx_ref_geo_niveau", "niveau"),
        # idx_ref_geo_nom_trgm : à créer manuellement en migration (extension pg_trgm)
    )

    parent: Mapped[RefGeoAdmin | None] = relationship(
        remote_side="RefGeoAdmin.id_geo", back_populates="enfants"
    )
    enfants: Mapped[list[RefGeoAdmin]] = relationship(back_populates="parent")

    localites: Mapped[list[Localite]] = relationship(back_populates="ref_geo")


class Localite(Base):
    """Localité métier (village/campement) rattachée à un nœud de niveau localite."""

    __tablename__ = "localite"

    id_localite: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_geo: Mapped[int] = mapped_column(
        Integer, ForeignKey("ref_geo_admin.id_geo", ondelete="RESTRICT"), nullable=False
    )
    nom_usage: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude_centre: Mapped[float | None] = mapped_column()
    longitude_centre: Mapped[float | None] = mapped_column()
    # geom_centre : colonne GENERATED, non déclarée en ORM (ajoutée en migration)
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
        # idx_localite_geom : GIST sur colonne générée, créé en migration
        # idx_localite_nom_trgm : GIN pg_trgm, créé en migration
        Index("idx_localite_metadata", "metadata", postgresql_using="gin"),
    )

    ref_geo: Mapped[RefGeoAdmin] = relationship(back_populates="localites")
    alias: Mapped[list[LocaliteAlias]] = relationship(
        back_populates="localite", cascade="all, delete-orphan"
    )
    ouvrages: Mapped[list[Ouvrage]] = relationship(back_populates="localite")
    cgpes: Mapped[list[CGPE]] = relationship(back_populates="localite")
    lignes_ingerees: Mapped[list[LigneIngeree]] = relationship(back_populates="localite")


class LocaliteAlias(Base):
    """Alias de noms de localités pour le rapprochement flou."""

    __tablename__ = "localite_alias"

    id_alias: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_localite: Mapped[int] = mapped_column(
        Integer, ForeignKey("localite.id_localite", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(String(150), nullable=False)
    source_alias: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        UniqueConstraint("id_localite", "alias", name="uq_alias_localite"),
        # idx_alias_trgm : GIN pg_trgm, créé en migration
    )

    localite: Mapped[Localite] = relationship(back_populates="alias")


# =====================================================================
# 2. INGESTION
# =====================================================================


class Fichier(Base):
    """Fichier reçu (Excel, CSV...). hash_sha256 non unique."""

    __tablename__ = "fichier"

    id_fichier: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_source: Mapped[int] = mapped_column(
        Integer, ForeignKey("source.id_source", ondelete="RESTRICT"), nullable=False
    )
    nom_fichier_original: Mapped[str] = mapped_column(String(255), nullable=False)
    chemin_stockage: Mapped[str] = mapped_column(Text, nullable=False)
    hash_sha256: Mapped[str | None] = mapped_column(String(64))
    taille_octets: Mapped[int | None] = mapped_column(BigInteger)
    date_reception: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    date_ingestion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="en_attente")
    nb_feuilles: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    nb_lignes_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    est_reingestion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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
    type_contenu: Mapped[str] = mapped_column(String(20), nullable=False, default="inconnu")
    nb_lignes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    nb_lignes_valides: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    statut_ingestion: Mapped[str] = mapped_column(String(20), nullable=False, default="en_attente")
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
        UniqueConstraint("id_fichier", "index_feuille", name="uq_feuille_fichier_index"),
        Index("idx_feuille_fichier", "id_fichier"),
    )

    fichier: Mapped[Fichier] = relationship(back_populates="feuilles")
    lignes: Mapped[list[LigneIngeree]] = relationship(
        back_populates="feuille", cascade="all, delete-orphan"
    )
    runs: Mapped[list[IngestionRun]] = relationship(back_populates="feuille")


class IngestionRun(Base):
    """Exécution d'ingestion avec paramètres choisis par l'utilisateur."""

    __tablename__ = "ingestion_run"

    id_run: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_fichier: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fichier.id_fichier", ondelete="CASCADE"), nullable=False
    )
    id_feuille: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("feuille.id_feuille", ondelete="CASCADE")
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="complet")
    limite_lignes: Mapped[int | None] = mapped_column(Integer)
    ligne_debut: Mapped[int | None] = mapped_column(Integer)
    ligne_fin: Mapped[int | None] = mapped_column(Integer)
    nb_lignes_ingerees: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="en_cours")
    message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("mode IN ('complet','echantillon','plage')", name="ingestion_run_mode_check"),
        CheckConstraint(
            "statut IN ('en_cours','termine','erreur','annule')",
            name="ingestion_run_statut_check",
        ),
        CheckConstraint(
            "(mode = 'complet' AND limite_lignes IS NULL "
            "AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'echantillon' AND limite_lignes IS NOT NULL "
            "AND ligne_debut IS NULL AND ligne_fin IS NULL) "
            "OR (mode = 'plage' AND limite_lignes IS NULL "
            "AND ligne_debut IS NOT NULL AND ligne_fin IS NOT NULL "
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
    """Ligne brute normalisée issue d'une feuille."""

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

    district_brut: Mapped[str | None] = mapped_column(String(150))
    region_brute: Mapped[str | None] = mapped_column(String(150))
    departement_brut: Mapped[str | None] = mapped_column(String(150))
    sous_prefecture_brute: Mapped[str | None] = mapped_column(String(150))
    localite_brute: Mapped[str | None] = mapped_column(String(150))
    type_localite_brut: Mapped[str | None] = mapped_column(String(30))

    latitude_decimal: Mapped[float | None] = mapped_column()
    longitude_decimal: Mapped[float | None] = mapped_column()
    # geom : colonne GENERATED, ajoutée en migration

    type_ouvrage_brut: Mapped[str | None] = mapped_column(String(50))
    etat_ouvrage_brut: Mapped[str | None] = mapped_column(String(50))
    annee_projet: Mapped[int | None] = mapped_column(Integer)
    bailleur_brut: Mapped[str | None] = mapped_column(String(150))
    type_financement_brut: Mapped[str | None] = mapped_column(String(50))
    a_cgpe: Mapped[bool | None] = mapped_column(Boolean)

    statut_qualite: Mapped[str] = mapped_column(String(30), nullable=False, default="ok")
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
        UniqueConstraint("id_run", "num_ligne_source", name="uq_ligne_run_num"),
        Index("idx_ligne_feuille", "id_feuille"),
        Index("idx_ligne_run", "id_run"),
        # idx_ligne_geom : GIST sur colonne générée, créé en migration
        Index("idx_ligne_statut_qualite", "statut_qualite"),
        Index("idx_ligne_localite", "id_localite"),
        Index("idx_ligne_type_ouvrage", "type_ouvrage_brut"),
        Index("idx_ligne_donnees_brutes", "donnees_brutes", postgresql_using="gin"),
        Index("idx_ligne_ouvrage", "id_ouvrage_consolide"),
    )

    feuille: Mapped[Feuille] = relationship(back_populates="lignes")
    run: Mapped[IngestionRun | None] = relationship(back_populates="lignes")
    localite: Mapped[Localite | None] = relationship(back_populates="lignes_ingerees")
    ouvrage_consolide: Mapped[Ouvrage | None] = relationship(back_populates="lignes_sources")


# =====================================================================
# 3. MÉTIER CONSOLIDÉ
# =====================================================================


class Ouvrage(Base):
    """Ouvrage consolidé (dédoublonné)."""

    __tablename__ = "ouvrage"

    id_ouvrage: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code_ouvrage: Mapped[str | None] = mapped_column(String(100))
    id_localite: Mapped[int] = mapped_column(
        Integer, ForeignKey("localite.id_localite", ondelete="RESTRICT"), nullable=False
    )
    id_type_ouvrage: Mapped[int] = mapped_column(
        Integer, ForeignKey("type_ouvrage.id_type_ouvrage", ondelete="RESTRICT"), nullable=False
    )
    etat: Mapped[str] = mapped_column(String(20), nullable=False, default="inconnu")
    annee_realisation: Mapped[int | None] = mapped_column(Integer)
    latitude_decimal: Mapped[float | None] = mapped_column()
    longitude_decimal: Mapped[float | None] = mapped_column()
    # geom : colonne GENERATED, ajoutée en migration
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
            "etat IN ('fonctionnel','en_panne','abandonne','inconnu')",
            name="ouvrage_etat_check",
        ),
        Index("idx_ouvrage_localite", "id_localite"),
        Index("idx_ouvrage_type", "id_type_ouvrage"),
        # idx_ouvrage_geom : GIST sur colonne générée, créé en migration
        Index("idx_ouvrage_etat", "etat"),
        Index(
            "idx_ouvrage_code",
            "code_ouvrage",
            postgresql_where="code_ouvrage IS NOT NULL",
        ),
        Index("idx_ouvrage_metadata", "metadata", postgresql_using="gin"),
    )

    localite: Mapped[Localite] = relationship(back_populates="ouvrages")
    type_ouvrage: Mapped[TypeOuvrage] = relationship(back_populates="ouvrages")
    cgpes: Mapped[list[CGPE]] = relationship(back_populates="ouvrage")
    financements: Mapped[list[OuvrageProjet]] = relationship(
        back_populates="ouvrage", cascade="all, delete-orphan"
    )
    lignes_sources: Mapped[list[LigneIngeree]] = relationship(back_populates="ouvrage_consolide")


class CGPE(Base):
    """Comité de gestion de point d'eau."""

    __tablename__ = "cgpe"

    id_cgpe: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_localite: Mapped[int] = mapped_column(
        Integer, ForeignKey("localite.id_localite", ondelete="CASCADE"), nullable=False
    )
    id_ouvrage: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("ouvrage.id_ouvrage", ondelete="SET NULL")
    )
    existe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
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
        Index("idx_cgpe_metadata", "metadata", postgresql_using="gin"),
    )

    localite: Mapped[Localite] = relationship(back_populates="cgpes")
    ouvrage: Mapped[Ouvrage | None] = relationship(back_populates="cgpes")


class ProjetFinancement(Base):
    """Projet de financement porté par un bailleur ou l'État."""

    __tablename__ = "projet_financement"

    id_projet: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom_projet: Mapped[str] = mapped_column(String(255), nullable=False)
    annee: Mapped[int | None] = mapped_column(Integer)
    id_source_financeur: Mapped[int] = mapped_column(
        Integer, ForeignKey("source.id_source", ondelete="RESTRICT"), nullable=False
    )
    type_financement: Mapped[str] = mapped_column(String(20), nullable=False)
    montant: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    devise: Mapped[str | None] = mapped_column(String(3), server_default="XOF")
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
        Index("idx_projet_source", "id_source_financeur"),
        Index("idx_projet_annee", "annee"),
    )

    financeur: Mapped[Source] = relationship(back_populates="projets_finances")
    ouvrages: Mapped[list[OuvrageProjet]] = relationship(
        back_populates="projet", cascade="all, delete-orphan"
    )


class OuvrageProjet(Base):
    """Association N..N Ouvrage–Projet avec rôle."""

    __tablename__ = "ouvrage_projet"

    id_ouvrage: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ouvrage.id_ouvrage", ondelete="CASCADE"), primary_key=True
    )
    id_projet: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projet_financement.id_projet", ondelete="CASCADE"),
        primary_key=True,
    )
    role_financement: Mapped[str] = mapped_column(String(20), nullable=False, default="principal")

    __table_args__ = (
        CheckConstraint(
            "role_financement IN ('principal','co_financement')",
            name="ouvrage_projet_role_check",
        ),
        Index("idx_ouvrage_projet_projet", "id_projet"),
    )

    ouvrage: Mapped[Ouvrage] = relationship(back_populates="financements")
    projet: Mapped[ProjetFinancement] = relationship(back_populates="ouvrages")