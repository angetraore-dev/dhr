-- =====================================================================
-- Bible du projet DHR — Schéma cible (v1.0)
-- Généré à partir de la section 2 de la Bible.
--
-- Ce fichier est la RÉFÉRENCE du schéma. Il est reproduit à l'identique
-- par la migration Alembic `0001_initial.py`. En cas de divergence, c'est
-- ce fichier qui fait foi.
--
-- Ordre d'exécution :
--   1. Extensions
--   2. Fonctions (geom_from_latlon, trg_set_updated_at, trg_check_localite_geo)
--   3. Tables (référentiels → ingestion → métier)
--   4. Contraintes et index (inclus dans les CREATE TABLE)
--   5. Triggers (après les tables)
--   6. Vues
--   7. Seed (sources)
-- =====================================================================

-- =====================================================================
-- 1. EXTENSIONS
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- =====================================================================
-- 2. FONCTIONS
-- =====================================================================

-- Convertit un couple (lat, lon) décimal en geometry(Point, 4326).
-- Retourne NULL si lat/lon NULL, hors bornes, ou (0, 0).
-- IMMUTABLE STRICT : requis pour les colonnes générées.
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

-- Trigger générique : met NEW.updated_at = now() à chaque UPDATE.
-- Créé table par table (7 tables).
CREATE OR REPLACE FUNCTION trg_set_updated_at()
    RETURNS trigger
    LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- Trigger : vérifie que localite.id_geo pointe vers un nœud niveau='localite'.
-- Empêche les erreurs de rattachement à une région ou un département.
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

-- =====================================================================
-- 3. TABLES — GROUPE A : RÉFÉRENTIELS
-- =====================================================================

-- Émetteur de fichiers (ONEP, SODECI, UNICEF, BAD, LONACI, État de CI...)
CREATE TABLE source (
                        id_source    serial PRIMARY KEY,
                        nom          varchar(100) NOT NULL,
                        type_source  varchar(30)  NOT NULL,
                        actif        boolean      NOT NULL DEFAULT true,
                        commentaire  text,
                        created_at   timestamptz  NOT NULL DEFAULT now(),
                        updated_at   timestamptz  NOT NULL DEFAULT now(),
                        CONSTRAINT source_type_source_check
                            CHECK (type_source IN ('public','prive','bailleur','etat','autre')),
                        CONSTRAINT uq_source_nom UNIQUE (nom)
);

-- Référentiel administratif hiérarchique (district → localité)
CREATE TABLE ref_geo_admin (
                               id_geo         serial PRIMARY KEY,
                               niveau         varchar(20)  NOT NULL,
                               nom            varchar(150) NOT NULL,
                               parent_id      integer,
                               code_officiel  varchar(50),
                               type_localite  varchar(20),
                               created_at     timestamptz  NOT NULL DEFAULT now(),
                               updated_at     timestamptz  NOT NULL DEFAULT now(),
                               CONSTRAINT ref_geo_admin_niveau_check
                                   CHECK (niveau IN ('district','region','departement','sous_prefecture','localite')),
                               CONSTRAINT ref_geo_admin_type_localite_check
                                   CHECK (type_localite IS NULL OR type_localite IN ('village','campement','autre')),
                               CONSTRAINT chk_ref_geo_type_localite
                                   CHECK ((niveau <> 'localite' AND type_localite IS NULL) OR (niveau = 'localite')),
                               CONSTRAINT chk_ref_geo_parent
                                   CHECK ((niveau = 'district' AND parent_id IS NULL)
                                       OR (niveau <> 'district' AND parent_id IS NOT NULL)),
                               CONSTRAINT uq_ref_geo_parent_nom_niveau UNIQUE (parent_id, nom, niveau),
                               CONSTRAINT ref_geo_admin_parent_id_fkey
                                   FOREIGN KEY (parent_id) REFERENCES ref_geo_admin(id_geo) ON DELETE RESTRICT
);

CREATE INDEX idx_ref_geo_niveau ON ref_geo_admin (niveau);
CREATE INDEX idx_ref_geo_parent ON ref_geo_admin (parent_id);
CREATE INDEX idx_ref_geo_nom_trgm ON ref_geo_admin USING gin (nom gin_trgm_ops);

-- Entité métier village / campement
CREATE TABLE localite (
                          id_localite       serial PRIMARY KEY,
                          id_geo            integer      NOT NULL,
                          nom_usage         varchar(150) NOT NULL,
                          latitude_centre   double precision,
                          longitude_centre  double precision,
                          commentaire       text,
                          metadata          jsonb        NOT NULL DEFAULT '{}'::jsonb,
                          created_at        timestamptz  NOT NULL DEFAULT now(),
                          updated_at        timestamptz  NOT NULL DEFAULT now(),
                          geom_centre       geometry(Point, 4326)
                              GENERATED ALWAYS AS (geom_from_latlon(latitude_centre, longitude_centre)) STORED,
                          CONSTRAINT localite_id_geo_fkey
                              FOREIGN KEY (id_geo) REFERENCES ref_geo_admin(id_geo) ON DELETE RESTRICT
);

CREATE INDEX idx_localite_geo ON localite (id_geo);
CREATE INDEX idx_localite_geom ON localite USING gist (geom_centre);
CREATE INDEX idx_localite_nom_trgm ON localite USING gin (nom_usage gin_trgm_ops);
CREATE INDEX idx_localite_metadata ON localite USING gin (metadata);

-- Variantes de noms pour le rapprochement (V2, vide au MVP)
CREATE TABLE localite_alias (
                                id_alias     serial PRIMARY KEY,
                                id_localite  integer      NOT NULL,
                                alias        varchar(150) NOT NULL,
                                source_alias varchar(100),
                                CONSTRAINT uq_alias_localite UNIQUE (id_localite, alias),
                                CONSTRAINT localite_alias_id_localite_fkey
                                    FOREIGN KEY (id_localite) REFERENCES localite(id_localite) ON DELETE CASCADE
);

CREATE INDEX idx_alias_trgm ON localite_alias USING gin (alias gin_trgm_ops);

-- =====================================================================
-- 4. TABLES — GROUPE B : INGESTION
-- =====================================================================

-- Fichier Excel uploadé (hash_sha256 non unique : réingestion légitime)
CREATE TABLE fichier (
                         id_fichier             bigserial PRIMARY KEY,
                         id_source              integer      NOT NULL,
                         nom_fichier_original   varchar(255) NOT NULL,
                         chemin_stockage        text         NOT NULL,
                         hash_sha256            varchar(64),
                         taille_octets          bigint,
                         date_reception         timestamptz  NOT NULL DEFAULT now(),
                         date_ingestion         timestamptz,
                         statut                 varchar(20)  NOT NULL DEFAULT 'en_attente',
                         nb_feuilles            integer      NOT NULL DEFAULT 0,
                         nb_lignes_total        integer      NOT NULL DEFAULT 0,
                         est_reingestion        boolean      NOT NULL DEFAULT false,
                         commentaire            text,
                         created_at             timestamptz  NOT NULL DEFAULT now(),
                         updated_at             timestamptz  NOT NULL DEFAULT now(),
                         CONSTRAINT fichier_statut_check
                             CHECK (statut IN ('en_attente','en_cours','ingere','partiel','erreur')),
                         CONSTRAINT fichier_id_source_fkey
                             FOREIGN KEY (id_source) REFERENCES source(id_source) ON DELETE RESTRICT
);

CREATE INDEX idx_fichier_source ON fichier (id_source);
CREATE INDEX idx_fichier_date ON fichier (date_reception);
CREATE INDEX idx_fichier_hash ON fichier (hash_sha256);

-- Feuille d'un classeur Excel
CREATE TABLE feuille (
                         id_feuille         bigserial PRIMARY KEY,
                         id_fichier         bigint       NOT NULL,
                         nom_feuille        varchar(150) NOT NULL,
                         index_feuille      integer      NOT NULL,
                         type_contenu       varchar(20)  NOT NULL DEFAULT 'inconnu',
                         nb_lignes          integer      NOT NULL DEFAULT 0,
                         nb_lignes_valides  integer      NOT NULL DEFAULT 0,
                         statut_ingestion   varchar(20)  NOT NULL DEFAULT 'en_attente',
                         message_erreur     text,
                         created_at         timestamptz  NOT NULL DEFAULT now(),
                         CONSTRAINT feuille_type_contenu_check
                             CHECK (type_contenu IN ('ouvrages','cgpe','mixte','autre','inconnu')),
                         CONSTRAINT feuille_statut_ingestion_check
                             CHECK (statut_ingestion IN ('en_attente','en_cours','ingere','partiel','erreur')),
                         CONSTRAINT uq_feuille_fichier_index UNIQUE (id_fichier, index_feuille),
                         CONSTRAINT feuille_id_fichier_fkey
                             FOREIGN KEY (id_fichier) REFERENCES fichier(id_fichier) ON DELETE CASCADE
);

CREATE INDEX idx_feuille_fichier ON feuille (id_fichier);

-- Mapping validé (entête Excel → champ cible)
CREATE TABLE mapping_feuille (
                                 id_mapping             serial PRIMARY KEY,
                                 id_feuille             bigint       NOT NULL,
                                 entete_brut            varchar(255) NOT NULL,
                                 champ_cible            varchar(100),
                                 confiance              numeric(3,2),
                                 valide_par_utilisateur boolean      NOT NULL DEFAULT false,
                                 created_at             timestamptz  NOT NULL DEFAULT now(),
                                 CONSTRAINT mapping_feuille_confiance_check
                                     CHECK (confiance IS NULL OR (confiance >= 0 AND confiance <= 1)),
                                 CONSTRAINT uq_mapping_feuille_entete UNIQUE (id_feuille, entete_brut),
                                 CONSTRAINT mapping_feuille_id_feuille_fkey
                                     FOREIGN KEY (id_feuille) REFERENCES feuille(id_feuille) ON DELETE CASCADE
);

CREATE INDEX idx_mapping_feuille_feuille ON mapping_feuille (id_feuille);

-- Exécution d'ingestion (paramètres + statut)
CREATE TABLE ingestion_run (
                               id_run              bigserial PRIMARY KEY,
                               id_fichier          bigint       NOT NULL,
                               id_feuille          bigint,
                               mode                varchar(20)  NOT NULL DEFAULT 'complet',
                               limite_lignes       integer,
                               ligne_debut         integer,
                               ligne_fin           integer,
                               nb_lignes_ingerees  integer      NOT NULL DEFAULT 0,
                               statut              varchar(20)  NOT NULL DEFAULT 'en_cours',
                               message             text,
                               started_at          timestamptz  NOT NULL DEFAULT now(),
                               finished_at         timestamptz,
                               CONSTRAINT ingestion_run_mode_check
                                   CHECK (mode IN ('complet','echantillon','plage')),
                               CONSTRAINT ingestion_run_statut_check
                                   CHECK (statut IN ('en_cours','termine','erreur','annule')),
                               CONSTRAINT chk_run_mode_params CHECK (
                                   (mode = 'complet'     AND limite_lignes IS NULL     AND ligne_debut IS NULL     AND ligne_fin IS NULL)
                                       OR (mode = 'echantillon' AND limite_lignes IS NOT NULL AND ligne_debut IS NULL     AND ligne_fin IS NULL)
                                       OR (mode = 'plage'       AND limite_lignes IS NULL     AND ligne_debut IS NOT NULL AND ligne_fin IS NOT NULL
                                       AND ligne_fin >= ligne_debut)
                                   ),
                               CONSTRAINT ingestion_run_id_fichier_fkey
                                   FOREIGN KEY (id_fichier) REFERENCES fichier(id_fichier) ON DELETE CASCADE,
                               CONSTRAINT ingestion_run_id_feuille_fkey
                                   FOREIGN KEY (id_feuille) REFERENCES feuille(id_feuille) ON DELETE CASCADE
);

CREATE INDEX idx_run_fichier ON ingestion_run (id_fichier);
CREATE INDEX idx_run_feuille ON ingestion_run (id_feuille);
CREATE INDEX idx_run_statut ON ingestion_run (statut);

-- Ligne brute d'Excel (matière première de la consolidation)
CREATE TABLE ligne_ingeree (
                               id_ligne                bigserial PRIMARY KEY,
                               id_feuille              bigint       NOT NULL,
                               id_run                  bigint,
                               num_ligne_source        integer      NOT NULL,
                               donnees_brutes          jsonb        NOT NULL,
                               district_brut           varchar(150),
                               region_brute            varchar(150),
                               departement_brut        varchar(150),
                               sous_prefecture_brute   varchar(150),
                               localite_brute          varchar(150),
                               type_localite_brut      varchar(30),
                               latitude_decimal        double precision,
                               longitude_decimal       double precision,
                               type_ouvrage_brut       varchar(50),
                               etat_ouvrage_brut       varchar(50),
                               annee_projet            integer,
                               bailleur_brut           varchar(150),
                               type_financement_brut   varchar(50),
                               usage_ouvrage_brut      varchar(50),
                               a_cgpe                  boolean,
                               statut_qualite          varchar(30)  NOT NULL DEFAULT 'ok',
                               message_qualite         text,
                               id_localite             integer,
                               id_ouvrage_consolide    bigint,
                               created_at              timestamptz  NOT NULL DEFAULT now(),
                               geom                    geometry(Point, 4326)
                                   GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED,
                               CONSTRAINT ligne_ingeree_statut_qualite_check
                                   CHECK (statut_qualite IN ('ok','localite_non_resolue','geom_invalide',
                                                             'type_ouvrage_inconnu','rejete','doublon_suspect')),
                               CONSTRAINT uq_ligne_feuille_run_num UNIQUE (id_feuille, id_run, num_ligne_source),
                               CONSTRAINT ligne_ingeree_id_feuille_fkey
                                   FOREIGN KEY (id_feuille) REFERENCES feuille(id_feuille) ON DELETE CASCADE,
                               CONSTRAINT ligne_ingeree_id_run_fkey
                                   FOREIGN KEY (id_run) REFERENCES ingestion_run(id_run) ON DELETE SET NULL,
                               CONSTRAINT ligne_ingeree_id_localite_fkey
                                   FOREIGN KEY (id_localite) REFERENCES localite(id_localite) ON DELETE SET NULL,
                               CONSTRAINT ligne_ingeree_id_ouvrage_consolide_fkey
                                   FOREIGN KEY (id_ouvrage_consolide) REFERENCES ouvrage(id_ouvrage) ON DELETE SET NULL
);

CREATE INDEX idx_ligne_feuille ON ligne_ingeree (id_feuille);
CREATE INDEX idx_ligne_run ON ligne_ingeree (id_run);
CREATE INDEX idx_ligne_geom ON ligne_ingeree USING gist (geom);
CREATE INDEX idx_ligne_statut_qualite ON ligne_ingeree (statut_qualite);
CREATE INDEX idx_ligne_localite ON ligne_ingeree (id_localite);
CREATE INDEX idx_ligne_type_ouvrage ON ligne_ingeree (type_ouvrage_brut);
CREATE INDEX idx_ligne_usage_ouvrage ON ligne_ingeree (usage_ouvrage_brut);
CREATE INDEX idx_ligne_donnees_brutes ON ligne_ingeree USING gin (donnees_brutes);
CREATE INDEX idx_ligne_ouvrage ON ligne_ingeree (id_ouvrage_consolide);

-- =====================================================================
-- 5. TABLES — GROUPE C : MÉTIER CONSOLIDÉ
-- =====================================================================

-- Ouvrage consolidé (dédoublonné)
CREATE TABLE ouvrage (
                         id_ouvrage          bigserial PRIMARY KEY,
                         code_ouvrage        varchar(100),
                         id_localite         integer      NOT NULL,
                         nature_ouvrage      varchar(20),
                         type_alimentation   varchar(20),
                         realisation_par     varchar(20),
                         etat                varchar(20)  NOT NULL DEFAULT 'inconnu',
                         annee_realisation   integer,
                         latitude_decimal    double precision,
                         longitude_decimal   double precision,
                         commentaire         text,
                         metadata            jsonb        NOT NULL DEFAULT '{}'::jsonb,
                         qualite_eau         jsonb,
                         created_at          timestamptz  NOT NULL DEFAULT now(),
                         updated_at          timestamptz  NOT NULL DEFAULT now(),
                         geom                geometry(Point, 4326)
                             GENERATED ALWAYS AS (geom_from_latlon(latitude_decimal, longitude_decimal)) STORED,
                         CONSTRAINT ouvrage_nature_check
                             CHECK (nature_ouvrage IS NULL OR nature_ouvrage IN ('puits','forage','inconnu')),
                         CONSTRAINT ouvrage_alimentation_check
                             CHECK (type_alimentation IS NULL OR type_alimentation IN ('PMH','HVA','PEA','HV','AUTRE')),
                         CONSTRAINT ouvrage_realisation_check
                             CHECK (realisation_par IS NULL OR realisation_par IN ('public','prive','inconnu')),
                         CONSTRAINT ouvrage_etat_check
                             CHECK (etat IN ('fonctionnel','en_panne','abandonne','inconnu')),
                         CONSTRAINT ouvrage_id_localite_fkey
                             FOREIGN KEY (id_localite) REFERENCES localite(id_localite) ON DELETE RESTRICT
);

CREATE INDEX idx_ouvrage_code ON ouvrage (code_ouvrage) WHERE code_ouvrage IS NOT NULL;
CREATE INDEX idx_ouvrage_localite ON ouvrage (id_localite);
CREATE INDEX idx_ouvrage_etat ON ouvrage (etat);
CREATE INDEX idx_ouvrage_nature ON ouvrage (nature_ouvrage);
CREATE INDEX idx_ouvrage_alimentation ON ouvrage (type_alimentation);
CREATE INDEX idx_ouvrage_realisation ON ouvrage (realisation_par);
CREATE INDEX idx_ouvrage_geom ON ouvrage USING gist (geom);
CREATE INDEX idx_ouvrage_metadata ON ouvrage USING gin (metadata);
CREATE INDEX idx_ouvrage_qualite_eau ON ouvrage USING gin (qualite_eau);

-- Comité de Gestion de Point d'Eau (V2, vide au MVP)
CREATE TABLE cgpe (
                      id_cgpe        serial PRIMARY KEY,
                      id_localite    integer      NOT NULL,
                      id_ouvrage     bigint,
                      existe         boolean      NOT NULL DEFAULT true,
                      date_creation  date,
                      statut         varchar(20),
                      nb_membres     integer,
                      commentaire    text,
                      metadata       jsonb        NOT NULL DEFAULT '{}'::jsonb,
                      created_at     timestamptz  NOT NULL DEFAULT now(),
                      updated_at     timestamptz  NOT NULL DEFAULT now(),
                      CONSTRAINT cgpe_statut_check
                          CHECK (statut IS NULL OR statut IN ('fonctionnel','non_fonctionnel','inconnu')),
                      CONSTRAINT cgpe_id_localite_fkey
                          FOREIGN KEY (id_localite) REFERENCES localite(id_localite) ON DELETE CASCADE,
                      CONSTRAINT cgpe_id_ouvrage_fkey
                          FOREIGN KEY (id_ouvrage) REFERENCES ouvrage(id_ouvrage) ON DELETE SET NULL
);

CREATE INDEX idx_cgpe_localite ON cgpe (id_localite);
CREATE INDEX idx_cgpe_ouvrage ON cgpe (id_ouvrage);
CREATE INDEX idx_cgpe_metadata ON cgpe USING gin (metadata);

-- Projet de financement (V2, vide au MVP)
CREATE TABLE projet_financement (
                                    id_projet             bigserial PRIMARY KEY,
                                    nom_projet            varchar(255) NOT NULL,
                                    annee                 integer,
                                    id_source_financeur   integer      NOT NULL,
                                    type_financement      varchar(20)  NOT NULL,
                                    montant               numeric(18,2),
                                    devise                varchar(3)   DEFAULT 'XOF',
                                    commentaire           text,
                                    created_at            timestamptz  NOT NULL DEFAULT now(),
                                    updated_at            timestamptz  NOT NULL DEFAULT now(),
                                    CONSTRAINT projet_financement_type_check
                                        CHECK (type_financement IN ('etat','prive','partenariat','inconnu')),
                                    CONSTRAINT projet_financement_id_source_financeur_fkey
                                        FOREIGN KEY (id_source_financeur) REFERENCES source(id_source) ON DELETE RESTRICT
);

CREATE INDEX idx_projet_annee ON projet_financement (annee);
CREATE INDEX idx_projet_source ON projet_financement (id_source_financeur);

-- Association N..N ouvrage ↔ projet (V2, vide au MVP)
CREATE TABLE ouvrage_projet (
                                id_ouvrage         bigint      NOT NULL,
                                id_projet          bigint      NOT NULL,
                                role_financement   varchar(20) NOT NULL DEFAULT 'principal',
                                PRIMARY KEY (id_ouvrage, id_projet),
                                CONSTRAINT ouvrage_projet_role_check
                                    CHECK (role_financement IN ('principal','co_financement')),
                                CONSTRAINT ouvrage_projet_id_ouvrage_fkey
                                    FOREIGN KEY (id_ouvrage) REFERENCES ouvrage(id_ouvrage) ON DELETE CASCADE,
                                CONSTRAINT ouvrage_projet_id_projet_fkey
                                    FOREIGN KEY (id_projet) REFERENCES projet_financement(id_projet) ON DELETE CASCADE
);

CREATE INDEX idx_ouvrage_projet_projet ON ouvrage_projet (id_projet);

-- =====================================================================
-- 6. TRIGGERS (après toutes les tables)
-- =====================================================================

CREATE TRIGGER set_updated_at BEFORE UPDATE ON source
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON ref_geo_admin
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON localite
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON fichier
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON ouvrage
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON cgpe
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON projet_financement
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER check_localite_geo BEFORE INSERT OR UPDATE OF id_geo ON localite
    FOR EACH ROW EXECUTE FUNCTION trg_check_localite_geo();

-- =====================================================================
-- 7. VUES
-- =====================================================================

-- Points bruts d'un fichier (mode "Par fichier" de la carte).
-- Exclut les feuilles de localités.
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
    );

-- Points consolidés (mode "Tous" de la carte).
-- Expose 4 niveaux : région, département, sous-préfecture, localité.
-- Pas de district (réforme territoriale).
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
WHERE o.geom IS NOT NULL;

-- Tableau de bord qualité par fichier.
-- nb_rejetes est calculé par différence (les rejets ne sont pas stockés).
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
GROUP BY f.id_fichier, f.nom_fichier_original, s.nom, f.statut, f.nb_lignes_total;

-- =====================================================================
-- 8. SEED — Sources
-- =====================================================================
INSERT INTO source (nom, type_source) VALUES
                                          ('ONEP',    'public'),
                                          ('SODECI',  'prive'),
                                          ('UNICEF',  'bailleur'),
                                          ('BAD',     'bailleur'),
                                          ('LONACI',  'public'),
                                          ('ETAT_CI', 'etat')
ON CONFLICT (nom) DO NOTHING;