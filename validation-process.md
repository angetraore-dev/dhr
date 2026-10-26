
```bash
# 1. Copier le template d'env
cp .env.example .env

# 2. (Optionnel) Générer un JWT_SECRET robuste
# openssl rand -hex 32  → coller dans .env

# 3. Builder et démarrer
docker compose up -d --build

# 4. Attendre que tout soit healthy (10-20s)
docker compose ps

# 5. Vérifier le back
curl http://localhost:8000/health
# Attendu : {"status":"ok","db":true,"version":"0.1.0","env":"development"}

# 6. Vérifier la doc Swagger
# Ouvrir http://localhost:8000/docs dans un navigateur

# 7. Vérifier le front
# Ouvrir http://localhost:5173 dans un navigateur
# Attendu : page "DHR — Ouvrages hydrauliques ruraux"

# 8. Vérifier la DB et le schéma
docker compose exec db psql -U dhr -d dhr -c "\dt"
# Attendu : les 13 tables du schema.sql

docker compose exec db psql -U dhr -d dhr -c "SELECT code, libelle FROM type_ouvrage;"
# Attendu : PMH, HV, HVA, PEA, AUTRE

ls backend/alembic/versions/
# Attendu : .gitkeep (ou vide)

ls backend/alembic/
# Attendu : env.py  script.py.mako  versions/

ls backend/
# Attendu : alembic.ini  alembic/  app/  Dockerfile  entrypoint.sh  pyproject.toml

ls backend/app/
# Attendu : __init__.py  config.py  db.py  main.py  models.py

```

Dans le message suivant, je te donnerai :

    Les commandes pour :

        Mettre à jour docker-compose.yml (monter alembic/)

        Recréer les containers (docker compose up -d --build)

        Lancer alembic revision --autogenerate -m "initial schema"

        Inspecter le fichier généré dans alembic/versions/

    Le code des ajouts manuels à insérer dans la migration :

        Extensions

        Fonctions

        Triggers

        Colonnes générées

        Index GIST + trigram

        Vues

        Seed

    La procédure de validation :

        alembic upgrade head → succès

        \dt → 13 tables

        \dv → 3 vues

        \df → 3 fonctions

        \d ligne_ingeree → colonne geom présente

        Test de la fonction geom_from_latlon(-5.3, 4.0)