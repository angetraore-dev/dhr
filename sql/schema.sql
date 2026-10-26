-- =====================================================================
-- schema.sql — Base de données DHR
-- Centralisation des ouvrages hydrauliques ruraux
-- PostgreSQL 14+ / PostGIS 3+
-- =====================================================================
-- Ordre d'exécution : extensions → fonctions → référentiels → ingestion
--                     → métier → triggers → vues → seed → migrations
-- Idempotent : peut être réexécuté sans casser une base existante
-- =====================================================================

\set ON_ERROR_STOP on

-- =====================================================================
-- 1. EXTENSIONS
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- postgis_topology : NON retenu (MVP, points isolés)

-- =====================================================================
-- 2. FONCTIONS UTILITAIRES
-- =====================================================================

-- 2.1 Conversion lat/lon décimal → geometry(Point,4326)
CREATE OR REPLACE FUNCTION geom_from_latlon(lat double precision, lon double precision)
    RETURNS geometry(Point,4326) AS $$
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

COMMENT ON FUNCTION geom_from_latlon(double precision, double precision)
    IS 'Convertit lat/lon décimaux en geometry(Point,4326). Rejette bornes invalides et (0,0).';

-- 2.2 Trigger générique updated_at
CREATE OR REPLACE FUNCTION trg_set_updated_at()
    RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2.3 Trigger : localite.id_geo doit être de niveau 'localite'
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

-- =====================================================================
-- 3. RÉFÉRENTIELS
-- =====================================================================

-- 3.1 source
CREATE TABLE IF NOT EXISTS source (
                                      id_source        serial PRIMARY KEY,
                                      nom              varchar(100) NOT NULL UNIQUE,
                                      type_source      varchar(30)  NOT NULL
                                          CHECK (type_source IN ('public','prive','bailleur','etat','autre')),
                                      actif            boolean NOT NULL DEFAULT true,
                                      commentaire      text,
                                      created_at       timestamptz NOT NULL DEFAULT now(),
                                      updated_at       timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE source IS 'Émetteur de fichiers : structure publique, privée, bailleur, État.';

-- 3.2 type_ouvrage
CREATE TABLE IF NOT EXISTS type_ouvrage (
                                            id_type_ouvrage  serial PRIMARY KEY,
                                            code             varchar(20) NOT NULL UNIQUE,
                                            libelle          varchar(100) NOT NULL,
                                            description      text,
                                            actif            boolean NOT NULL DEFAULT true
);

COMMENT ON TABLE type_ouvrage IS 'Nomenclature contrôlée : PMH, HV, HVA, PEA, AUTRE.';

-- 3.3 ref_geo_admin (hiérarchie auto-référencée)
CREATE TABLE IF NOT EXISTS ref_geo_admin (
                                             id_geo           serial PRIMARY KEY,
                                             niveau           varchar(20) NOT NULL
                                                 CHECK (niveau IN ('district','region','departement','sous_prefecture','localite')),
                                             nom              varchar(150) NOT NULL,
                                             parent_id        integer REFERENCES ref_geo_admin(id_geo) ON DELETE RESTRICT,
                                             code_officiel    varchar(50),
                                             type_localite    varchar(20)
                                                 CHECK (type_localite IS NULL OR type_localite IN ('village','campement','autre')),
                                             created_at       timestamptz NOT NULL DEFAULT now(),
                                             updated_at       timestamptz NOT NULL DEFAULT now(),
                                             CONSTRAINT chk_ref_geo_type_localite
                                                 CHECK ((niveau = 'localite'     AND type_localite IS NOT NULL)
                                                     OR (niveau <> 'localite'    AND type_localite IS NULL)),
                                             CONSTRAINT chk_ref_geo_parent
                                                 CHECK ((niveau = 'district'  AND parent_id IS NULL)
                                                     OR (niveau <> 'district' AND parent_id IS NOT NULL)),
                                             CONSTRAINT uq_ref_geo_parent_nom_niveau
                                                 UNIQUE (parent_id, nom, niveau)
);

CREATE INDEX IF NOT EXISTS idx_ref_geo_parent
    ON ref_geo_admin(parent_id);
CREATE INDEX IF NOT EXISTS idx_ref_geo_niveau
    ON ref_geo_admin(niveau);
CREATE INDEX IF NOT EXISTS idx_ref_geo_nom_trgm
    ON ref_geo_admin USING gin (nom gin_trgm_ops);

COMMENT ON TABLE ref_geo_admin
    IS 'Référentiel administratif hiérarchique : district→région→département→sous-préf→localité.';

-- 3.4 localite (entité métier rattachée au référentiel)
CREATE TABLE IF NOT EXISTS localite (
                                        id_localite      serial PRIMARY KEY,
                                        id_geo           integer NOT NULL REFERENCES ref_geo_admin(id_geo) ON DELETE RESTRICT,
                                        nom_usage        varchar(150) NOT NULL,
                                        latitude_centre  double precision,
                                        longitude_centre double precision,
                                        geom_centre      geometry(Point,4326)
                                            GENERATED ALWAYS AS (geom_from_latlon(latitude_centre, longitude_centre)) STORED,
                                        commentaire      text,
                                        metadata         jsonb NOT NULL DEFAULT '{}'::jsonb,
                                        created_at       timestamptz NOT NULL DEFAULT now(),
                                        updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_localite_geo
    ON localite(id_geo);
CREATE INDEX IF NOT EXISTS idx_localite_geom
    ON localite USING gist (geom_centre);
CREATE INDEX IF NOT EXISTS idx_localite_nom_trgm
    ON localite USING gin (nom_usage gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_localite_metadata
    ON localite USING gin (metadata);

COMMENT ON TABLE localite
    IS 'Localité métier (village/campement) rattachée à un noeud ref_geo_admin de niveau localite.';
COMMENT ON COLUMN localite.metadata
    IS 'Attributs complémentaires non mappés (convention : docs/metadata_conventions.md).';

-- 3.5 localite_alias
CREATE TABLE IF NOT EXISTS localite_alias (
                                              id_alias         serial PRIMARY KEY,
                                              id_localite      integer NOT NULL REFERENCES localite(id_localite) ON DELETE CASCADE,
                                              alias            varchar(150) NOT NULL,
                                              source_alias     varchar(100),
                                              CONSTRAINT uq_alias_localite UNIQUE (id_localite, alias)
);

CREATE INDEX IF NOT EXISTS idx_alias_trgm
    ON localite_alias USING gin (alias gin_trgm_ops);

COMMENT ON TABLE localite_alias
    IS 'Alias de noms de localités pour le rapprochement flou (ex. "Camp X" vs "Campement de X").';

-- =====================================================================
-- 4. INGESTION
-- =====================================================================

-- 4.1 fichier
CREATE TABLE IF NOT EXISTS fichier (
                                       id_fichier           bigserial PRIMARY KEY,
                                       id_source            integer NOT NULL REFERENCES source(id_source) ON DELETE RESTRICT,
                                       nom_fichier_original varchar(255) NOT NULL,
                                       chemin_stockage      text NOT NULL,
                                       hash_sha256          char(64),                 -- PAS UNIQUE : réingestion légitime
                                       taille_octets        bigint,
                                       date_reception       timestamptz NOT NULL DEFAULT now(),
                                       date_ingestion       timestamptz,
                                       statut               varchar(20) NOT NULL DEFAULT 'en_attente'
                                           CHECK (statut IN ('en_attente','en_cours','ingere','partiel','erreur')),
                                       nb_feuilles          integer DEFAULT 0,
                                       nb_lignes_total      integer DEFAULT 0,
                                       est_reingestion      boolean NOT NULL DEFAULT false,
                                       commentaire          text,
                                       created_at           timestamptz NOT NULL DEFAULT now(),
                                       updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fichier_source  ON fichier(id_source);
CREATE INDEX IF NOT EXISTS idx_fichier_date    ON fichier(date_reception DESC);
CREATE INDEX IF NOT EXISTS idx_fichier_hash    ON fichier(hash_sha256);

COMMENT ON TABLE fichier IS 'Fichier reçu (Excel, CSV...). hash_sha256 non unique (réingestion possible).';

-- 4.2 feuille
CREATE TABLE IF NOT EXISTS feuille (
                                       id_feuille       bigserial PRIMARY KEY,
                                       id_fichier       bigint NOT NULL REFERENCES fichier(id_fichier) ON DELETE CASCADE,
                                       nom_feuille      varchar(150) NOT NULL,
                                       index_feuille    integer NOT NULL,
                                       type_contenu     varchar(20) NOT NULL DEFAULT 'inconnu'
                                           CHECK (type_contenu IN ('ouvrages','cgpe','mixte','autre','inconnu')),
                                       nb_lignes        integer DEFAULT 0,
                                       nb_lignes_valides integer DEFAULT 0,
                                       statut_ingestion varchar(20) NOT NULL DEFAULT 'en_attente'
                                           CHECK (statut_ingestion IN ('en_attente','en_cours','ingere','partiel','erreur')),
                                       message_erreur   text,
                                       created_at       timestamptz NOT NULL DEFAULT now(),
                                       CONSTRAINT uq_feuille_fichier_index UNIQUE (id_fichier, index_feuille)
);

CREATE INDEX IF NOT EXISTS idx_feuille_fichier ON feuille(id_fichier);

COMMENT ON TABLE feuille IS 'Feuille d''un classeur Excel. Un fichier = 1..N feuilles.';

-- 4.3 ingestion_run
CREATE TABLE IF NOT EXISTS ingestion_run (
                                             id_run             bigserial PRIMARY KEY,
                                             id_fichier         bigint NOT NULL REFERENCES fichier(id_fichier) ON DELETE CASCADE,
                                             id_feuille         bigint REFERENCES feuille(id_feuille) ON DELETE CASCADE,
                                             mode               varchar(20) NOT NULL DEFAULT 'complet'
                                                 CHECK (mode IN ('complet','echantillon','plage')),
                                             limite_lignes      integer,
                                             ligne_debut        integer,
                                             ligne_fin          integer,
                                             nb_lignes_ingerees integer DEFAULT 0,
                                             statut             varchar(20) NOT NULL DEFAULT 'en_cours'
                                                 CHECK (statut IN ('en_cours','termine','erreur','annule')),
                                             message            text,
                                             started_at         timestamptz NOT NULL DEFAULT now(),
                                             finished_at        timestamptz,
                                             CONSTRAINT chk_run_mode_params CHECK (
                                                 (mode = 'complet'
                                                     AND limite_lignes IS NULL AND ligne_debut IS NULL AND ligne_fin IS NULL)
                                                     OR (mode = 'echantillon'
                                                     AND limite_lignes IS NOT NULL AND ligne_debut IS NULL AND ligne_fin IS NULL)
                                                     OR (mode = 'plage'
                                                     AND limite_lignes IS NULL
                                                     AND ligne_debut IS NOT NULL AND ligne_fin IS NOT NULL
                                                     AND ligne_fin >= ligne_debut)
                                                 )
);

CREATE INDEX IF NOT EXISTS idx_run_fichier ON ingestion_run(id_fichier);
CREATE INDEX IF NOT EXISTS idx_run_feuille ON ingestion_run(id_feuille);
CREATE INDEX IF NOT EXISTS idx_run_statut  ON ingestion_run(statut);

COMMENT ON TABLE ingestion_run
    IS 'Exécution d''ingestion avec paramètres choisis par l''utilisateur (mode, plage, limite).';

-- 4.4 ligne_ingeree
CREATE TABLE IF NOT EXISTS ligne_ingeree (
                                             id_ligne              bigserial PRIMARY KEY,
                                             id_feuille            bigint NOT NULL REFERENCES feuille(id_feuille) ON DELETE CASCADE,
                                             id_run                bigint REFERENCES ingestion_run(id_run) ON DELETE SET NULL,
                                             num_ligne_source      integer NOT NULL,

    -- Ligne Excel brute conservée (extensibilité bailleurs)
                                             donnees_brutes        jsonb NOT NULL,

    -- Champs normalisés extraits
                                             district_brut         varchar(150),
                                             region_brute          varchar(150),
                                             departement_brut      varchar(150),
                                             sous_prefecture_brute varchar(150),
                                             localite_brute        varchar(150),
                                             type_localite_brut    varchar(30),

                                             latitude_decimal      double precision,
                                             longitude_decimal     double precision,
                                             geom                  geometry(Point,4326)
                                                 GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED,

                                             type_ouvrage_brut     varchar(50),
                                             etat_ouvrage_brut     varchar(50),
                                             annee_projet          integer,
                                             bailleur_brut         varchar(150),
                                             type_financement_brut varchar(50),
                                             a_cgpe                boolean,

    -- Résultats rapprochement / qualité
                                             statut_qualite        varchar(30) NOT NULL DEFAULT 'ok'
                                                 CHECK (statut_qualite IN ('ok','localite_non_resolue','geom_invalide',
                                                                           'type_ouvrage_inconnu','rejete','doublon_suspect')),
                                             message_qualite       text,
                                             id_localite           integer REFERENCES localite(id_localite) ON DELETE SET NULL,
                                             id_ouvrage_consolide  bigint,   -- FK ajoutée après création de ouvrage
                                             created_at            timestamptz NOT NULL DEFAULT now(),

                                             CONSTRAINT uq_ligne_run_num UNIQUE (id_run, num_ligne_source)
);

CREATE INDEX IF NOT EXISTS idx_ligne_feuille         ON ligne_ingeree(id_feuille);
CREATE INDEX IF NOT EXISTS idx_ligne_run             ON ligne_ingeree(id_run);
CREATE INDEX IF NOT EXISTS idx_ligne_geom            ON ligne_ingeree USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_ligne_statut_qualite  ON ligne_ingeree(statut_qualite);
CREATE INDEX IF NOT EXISTS idx_ligne_localite        ON ligne_ingeree(id_localite);
CREATE INDEX IF NOT EXISTS idx_ligne_type_ouvrage    ON ligne_ingeree(type_ouvrage_brut);
CREATE INDEX IF NOT EXISTS idx_ligne_donnees_brutes  ON ligne_ingeree USING gin (donnees_brutes);
CREATE INDEX IF NOT EXISTS idx_ligne_ouvrage         ON ligne_ingeree(id_ouvrage_consolide);

COMMENT ON TABLE ligne_ingeree
    IS 'Ligne brute normalisée issue d''une feuille. Alimente la vue "par fichier" de l''UI carto.';

-- =====================================================================
-- 5. MÉTIER CONSOLIDÉ
-- =====================================================================

-- 5.1 ouvrage
CREATE TABLE IF NOT EXISTS ouvrage (
                                       id_ouvrage        bigserial PRIMARY KEY,
                                       code_ouvrage      varchar(100),                 -- nullable, non unique
                                       id_localite       integer NOT NULL REFERENCES localite(id_localite) ON DELETE RESTRICT,
                                       id_type_ouvrage   integer NOT NULL REFERENCES type_ouvrage(id_type_ouvrage) ON DELETE RESTRICT,
                                       etat              varchar(20) NOT NULL DEFAULT 'inconnu'
                                           CHECK (etat IN ('fonctionnel','en_panne','abandonne','inconnu')),
                                       annee_realisation integer,
                                       latitude_decimal  double precision,
                                       longitude_decimal double precision,
                                       geom              geometry(Point,4326)
                                           GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED,
                                       commentaire       text,
                                       metadata          jsonb NOT NULL DEFAULT '{}'::jsonb,
                                       created_at        timestamptz NOT NULL DEFAULT now(),
                                       updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ouvrage_localite ON ouvrage(id_localite);
CREATE INDEX IF NOT EXISTS idx_ouvrage_type     ON ouvrage(id_type_ouvrage);
CREATE INDEX IF NOT EXISTS idx_ouvrage_geom     ON ouvrage USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_ouvrage_etat     ON ouvrage(etat);
CREATE INDEX IF NOT EXISTS idx_ouvrage_code     ON ouvrage(code_ouvrage) WHERE code_ouvrage IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ouvrage_metadata ON ouvrage USING gin (metadata);

COMMENT ON TABLE ouvrage IS 'Ouvrage consolidé (dédoublonné). Alimente la vue "Tous" de l''UI carto.';
COMMENT ON COLUMN ouvrage.metadata
    IS 'Attributs complémentaires non mappés (convention : docs/metadata_conventions.md).';

-- FK différée depuis ligne_ingeree
ALTER TABLE ligne_ingeree
    DROP CONSTRAINT IF EXISTS fk_ligne_ouvrage;
ALTER TABLE ligne_ingeree
    ADD CONSTRAINT fk_ligne_ouvrage
        FOREIGN KEY (id_ouvrage_consolide) REFERENCES ouvrage(id_ouvrage) ON DELETE SET NULL;

-- 5.2 cgpe
CREATE TABLE IF NOT EXISTS cgpe (
                                    id_cgpe        serial PRIMARY KEY,
                                    id_localite    integer NOT NULL REFERENCES localite(id_localite) ON DELETE CASCADE,
                                    id_ouvrage     bigint REFERENCES ouvrage(id_ouvrage) ON DELETE SET NULL,
                                    existe         boolean NOT NULL DEFAULT true,
                                    date_creation  date,
                                    statut         varchar(20)
                                        CHECK (statut IS NULL OR statut IN ('fonctionnel','non_fonctionnel','inconnu')),
                                    nb_membres     integer,
                                    commentaire    text,
                                    metadata       jsonb NOT NULL DEFAULT '{}'::jsonb,
                                    created_at     timestamptz NOT NULL DEFAULT now(),
                                    updated_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cgpe_localite ON cgpe(id_localite);
CREATE INDEX IF NOT EXISTS idx_cgpe_ouvrage  ON cgpe(id_ouvrage);
CREATE INDEX IF NOT EXISTS idx_cgpe_metadata ON cgpe USING gin (metadata);

COMMENT ON TABLE cgpe IS 'Comité de gestion de point d''eau.';
COMMENT ON COLUMN cgpe.metadata
    IS 'Attributs complémentaires non mappés (convention : docs/metadata_conventions.md).';

-- 5.3 projet_financement
CREATE TABLE IF NOT EXISTS projet_financement (
                                                  id_projet           bigserial PRIMARY KEY,
                                                  nom_projet          varchar(255) NOT NULL,
                                                  annee               integer,
                                                  id_source_financeur integer NOT NULL REFERENCES source(id_source) ON DELETE RESTRICT,
                                                  type_financement    varchar(20) NOT NULL
                                                      CHECK (type_financement IN ('etat','prive','partenariat','inconnu')),
                                                  montant             numeric(18,2),
                                                  devise              char(3) DEFAULT 'XOF',
                                                  commentaire         text,
                                                  created_at          timestamptz NOT NULL DEFAULT now(),
                                                  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_projet_source ON projet_financement(id_source_financeur);
CREATE INDEX IF NOT EXISTS idx_projet_annee  ON projet_financement(annee);

COMMENT ON TABLE projet_financement IS 'Projet de financement porté par un bailleur ou l''État.';

-- 5.4 ouvrage_projet (N..N)
CREATE TABLE IF NOT EXISTS ouvrage_projet (
                                              id_ouvrage       bigint NOT NULL REFERENCES ouvrage(id_ouvrage) ON DELETE CASCADE,
                                              id_projet        bigint NOT NULL REFERENCES projet_financement(id_projet) ON DELETE CASCADE,
                                              role_financement varchar(20) NOT NULL DEFAULT 'principal'
                                                  CHECK (role_financement IN ('principal','co_financement')),
                                              PRIMARY KEY (id_ouvrage, id_projet)
);

CREATE INDEX IF NOT EXISTS idx_ouvrage_projet_projet ON ouvrage_projet(id_projet);

COMMENT ON TABLE ouvrage_projet
    IS 'Association N..N Ouvrage–Projet avec rôle (principal / co-financement).';

-- =====================================================================
-- 6. TRIGGERS updated_at
-- =====================================================================
DO $$
    DECLARE
        t text;
        tables text[] := ARRAY[
            'source','ref_geo_admin','localite','fichier',
            'ouvrage','cgpe','projet_financement'
            ];
    BEGIN
        FOREACH t IN ARRAY tables LOOP
                EXECUTE format('DROP TRIGGER IF EXISTS set_updated_at ON %I;', t);
                EXECUTE format(
                    'CREATE TRIGGER set_updated_at BEFORE UPDATE ON %I
                     FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();', t);
            END LOOP;
    END $$;

-- Trigger de cohérence localite.id_geo
DROP TRIGGER IF EXISTS check_localite_geo ON localite;
CREATE TRIGGER check_localite_geo
    BEFORE INSERT OR UPDATE OF id_geo ON localite
    FOR EACH ROW EXECUTE FUNCTION trg_check_localite_geo();

-- =====================================================================
-- 7. VUES (lecture seule pour l'UI carto)
-- =====================================================================

-- 7.1 Points par fichier (vue « par fichier »)
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
WHERE li.geom IS NOT NULL;

COMMENT ON VIEW v_points_par_fichier
    IS 'Alimente le sélecteur de fichier de l''UI carto. Filtre : WHERE id_fichier = :id.';

-- 7.2 Points consolidés (vue « Tous »)
CREATE OR REPLACE VIEW v_points_consolides AS
SELECT
    o.id_ouvrage,
    o.code_ouvrage,
    o.etat,
    t.code AS type_ouvrage,
    o.annee_realisation,
    l.nom_usage AS localite,
    g.nom       AS sous_prefecture,
    gp.nom      AS departement,
    gr.nom      AS region,
    gd.nom      AS district,
    o.latitude_decimal,
    o.longitude_decimal,
    o.geom
FROM ouvrage o
         JOIN type_ouvrage t ON t.id_type_ouvrage = o.id_type_ouvrage
         JOIN localite l     ON l.id_localite     = o.id_localite
         JOIN ref_geo_admin g   ON g.id_geo = l.id_geo
         LEFT JOIN ref_geo_admin gp ON gp.id_geo = g.parent_id
         LEFT JOIN ref_geo_admin gr ON gr.id_geo = gp.parent_id
         LEFT JOIN ref_geo_admin gd ON gd.id_geo = gr.parent_id
WHERE o.geom IS NOT NULL;

COMMENT ON VIEW v_points_consolides
    IS 'Alimente l''option "Tous" de l''UI carto (points dédoublonnés).';

-- 7.3 Qualité par fichier (tableau de bord DHR)
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
GROUP BY f.id_fichier, f.nom_fichier_original, s.nom, f.statut, f.nb_lignes_total;

COMMENT ON VIEW v_qualite_par_fichier
    IS 'Tableau de bord qualité d''ingestion par fichier.';

-- =====================================================================
-- 8. SEED MINIMAL (référentiels)
-- =====================================================================

-- 8.1 Types d'ouvrage
INSERT INTO type_ouvrage (code, libelle, description) VALUES
                                                          ('PMH',   'Pompe à motricité humaine',       'Forage équipé d''une pompe manuelle'),
                                                          ('HV',    'Hydraulique villageoise',          'Système d''adduction en eau potable villageois'),
                                                          ('HVA',   'Hydraulique villageoise améliorée','Système HV avec améliorations techniques'),
                                                          ('PEA',   'Poste d''eau autonome',            'Point d''eau autonome (souvent en zone urbaine)'),
                                                          ('AUTRE', 'Autre type d''ouvrage',            'À qualifier au cas par cas')
ON CONFLICT (code) DO NOTHING;

-- 8.2 Sources (à compléter par la DHR)
INSERT INTO source (nom, type_source, commentaire) VALUES
                                                       ('ONEP',   'public',    'Office National de l''Eau Potable'),
                                                       ('SODECI', 'prive',     'Société de Distribution d''Eau de Côte d''Ivoire'),
                                                       ('UNICEF', 'bailleur',  'Fonds des Nations Unies pour l''Enfance'),
                                                       ('BAD',    'bailleur',  'Banque Africaine de Développement'),
                                                       ('LONACI', 'public',    'Loterie Nationale de Côte d''Ivoire'),
                                                       ('ETAT_CI','etat',      'État de Côte d''Ivoire (Ministère de l''Hydraulique)')
ON CONFLICT (nom) DO NOTHING;

-- =====================================================================
-- 9. MIGRATIONS IDEMPOTENTES (pour bases existantes)
-- =====================================================================
-- Ajout de metadata sur localite / ouvrage / cgpe (si base antérieure)
ALTER TABLE localite ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE ouvrage  ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE cgpe     ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_localite_metadata ON localite USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_ouvrage_metadata  ON ouvrage  USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_cgpe_metadata     ON cgpe     USING gin (metadata);

-- =====================================================================
-- 10. FIN
-- =====================================================================
