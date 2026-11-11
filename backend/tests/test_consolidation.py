"""
Tests du service de consolidation.

Couvre :
- Création d'ouvrage (B6).
- Mise à jour d'ouvrage existant (dédoublonnage).
- `doublon_suspect` (B6.1) : code déjà vu + distance > 1 km.
- `type_ouvrage_inconnu` (B6.2) : nature/alim/réal tous inconnus.
- `qualite_eau` (B6.3) : extraction des indicateurs sanitaires.
- `_map_nature`, `_map_alimentation`, `_map_realisation`, `_map_etat`.
"""
from __future__ import annotations

import pytest

from app.models import IngestionRun, LigneIngeree, Ouvrage
from app.services.consolidation import (
    _extraire_qualite_eau,
    _map_alimentation,
    _map_etat,
    _map_nature,
    _map_realisation,
    consolider_lignes_run,
)


def _creer_ligne_ok(
    db, id_feuille, id_run, id_localite,
    localite_brute="LOC_TEST",
    lat=7.5, lon=-5.5,
    type_ouvrage_brut="Forage ADM",
    usage_ouvrage_brut="PMH",
    etat_ouvrage_brut="Fonctionnel",
    annee_projet=2020,
    donnees_brutes=None,
):
    ligne = LigneIngeree(
        id_feuille=id_feuille,
        id_run=id_run,
        num_ligne_source=1,
        donnees_brutes=donnees_brutes or {"Code ouvrage": "CODE001"},
        localite_brute=localite_brute,
        latitude_decimal=lat,
        longitude_decimal=lon,
        type_ouvrage_brut=type_ouvrage_brut,
        usage_ouvrage_brut=usage_ouvrage_brut,
        etat_ouvrage_brut=etat_ouvrage_brut,
        annee_projet=annee_projet,
        statut_qualite="ok",
        id_localite=id_localite,
    )
    db.add(ligne)
    db.flush()
    return ligne


class TestMapNature:
    def test_puits(self):
        assert _map_nature("Puits") == "puits"
        assert _map_nature("PUITS AMELIORE") == "puits"

    def test_forage(self):
        assert _map_nature("Forage ADM") == "forage"
        assert _map_nature("Sondage") == "forage"

    def test_inconnu(self):
        assert _map_nature("Autre") == "inconnu"
        assert _map_nature(None) == "inconnu"


class TestMapAlimentation:
    def test_nom_feuille_prioritaire(self):
        assert _map_alimentation("Forage", "PMH", nom_feuille="HVA") == "HVA"

    def test_type_ouvrage_brut(self):
        assert _map_alimentation("PMH", None) == "PMH"
        assert _map_alimentation("Hydraulique villageoise améliorée", None) == "HVA"

    def test_usage_ouvrage_brut(self):
        assert _map_alimentation(None, "PMH") == "PMH"
        assert _map_alimentation(None, "Point d'eau autonome") == "PEA"

    def test_autre(self):
        assert _map_alimentation("Inconnu", "Inconnu") == "AUTRE"


class TestMapRealisation:
    def test_type_ouvrage_adm(self):
        assert _map_realisation(None, "Forage ADM") == "public"
        assert _map_realisation(None, "SODECI") == "prive"

    def test_colonne_type_de_forage(self):
        assert _map_realisation({"Type de forage": "Public"}) == "public"
        assert _map_realisation({"Type de forage": "Privé"}) == "prive"

    def test_inconnu(self):
        assert _map_realisation(None, None) == "inconnu"


class TestMapEtat:
    def test_fonctionnel(self):
        assert _map_etat("Fonctionnel") == "fonctionnel"
        assert _map_etat("Bon état") == "fonctionnel"

    def test_en_panne(self):
        assert _map_etat("En panne") == "en_panne"
        assert _map_etat("Non fonctionnel") == "en_panne"

    def test_abandonne(self):
        assert _map_etat("Abandonné") == "abandonne"

    def test_inconnu(self):
        assert _map_etat(None) == "inconnu"


class TestExtraireQualiteEau:
    def test_indicateur_normalise(self):
        result = _extraire_qualite_eau({
            "Onchocercose": "Non",
            "Vers_Guinee": "Oui",
        })
        assert result is not None
        assert result["onchocercose"] == "Non"
        assert result["vers_de_guinee"] == "Oui"
        assert result["brut_Onchocercose"] == "Non"
        assert result["brut_Vers_Guinee"] == "Oui"

    def test_aucun_indicateur(self):
        result = _extraire_qualite_eau({
            "Localité": "LOC_TEST",
            "Latitude": 7.5,
        })
        assert result is None

    def test_mot_cle_generique(self):
        result = _extraire_qualite_eau({"Maladie": "Aucune"})
        assert result is not None
        assert "brut_Maladie" in result


class TestConsolidationLigne:
    def test_creation_ouvrage(
        self, db, localite_test, fichier_avec_feuille
    ):
        fichier, feuille = fichier_avec_feuille
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        ligne = _creer_ligne_ok(
            db, feuille.id_feuille, run.id_run, localite_test.id_localite
        )

        stats = consolider_lignes_run(db, run.id_run)

        assert stats["ouvrages_crees"] == 1
        assert ligne.id_ouvrage_consolide is not None

        ouvrage = db.get(Ouvrage, ligne.id_ouvrage_consolide)
        assert ouvrage.nature_ouvrage == "forage"
        assert ouvrage.type_alimentation == "PMH"
        assert ouvrage.realisation_par == "public"
        assert ouvrage.etat == "fonctionnel"
        assert ouvrage.metadata_["brut_Code ouvrage"] == "CODE001"

    def test_doublon_suspect(
        self, db, localite_test, fichier_avec_feuille
    ):
        """B6.1 : même code + distance > 1 km → doublon_suspect."""
        fichier, feuille = fichier_avec_feuille
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        # 1er ouvrage à (7.5, -5.5)
        ligne1 = _creer_ligne_ok(
            db, feuille.id_feuille, run.id_run, localite_test.id_localite,
            lat=7.5, lon=-5.5, donnees_brutes={"Code ouvrage": "CODE_DUP"},
        )
        consolider_lignes_run(db, run.id_run)

        # 2e ligne avec le même code mais à (8.5, -5.5) → ~111 km
        run2 = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run2)
        db.flush()
        ligne2 = _creer_ligne_ok(
            db, feuille.id_feuille, run2.id_run, localite_test.id_localite,
            lat=8.5, lon=-5.5, donnees_brutes={"Code ouvrage": "CODE_DUP"},
        )

        stats = consolider_lignes_run(db, run2.id_run)

        assert stats["doublons_suspects"] == 1
        assert ligne2.statut_qualite == "doublon_suspect"
        assert "CODE_DUP" in ligne2.message_qualite
        assert ligne2.id_ouvrage_consolide is None

    def test_type_ouvrage_inconnu(
        self, db, localite_test, fichier_avec_feuille
    ):
        """B6.2 : nature/alim/réal tous inconnus → type_ouvrage_inconnu."""
        fichier, feuille = fichier_avec_feuille
        feuille.nom_feuille = "FEUILLE_NEUTRE"
        run = IngestionRun(
            id_fichier=fichier.id_fichier, mode="complet", statut="en_cours"
        )
        db.add(run)
        db.flush()

        ligne = _creer_ligne_ok(
            db, feuille.id_feuille, run.id_run, localite_test.id_localite,
            type_ouvrage_brut=None,
            usage_ouvrage_brut=None,
            etat_ouvrage_brut=None,
        )
        # Pas de code ouvrage pour éviter le dédoublonnage
        ligne.donnees_brutes={}
        db.flush()

        stats = consolider_lignes_run(db, run.id_run)

        assert stats["ouvrages_crees"] == 1
        assert stats["attributs_indetermines"] == 1
        assert ligne.statut_qualite == "type_ouvrage_inconnu"
        # L'ouvrage est quand même créé
        assert ligne.id_ouvrage_consolide is not None