
#### Test de Migration
```bash
# 1. Reset la base (perte de données)
docker compose exec db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 2. Appliquer la migration
docker compose exec backend alembic upgrade head

# 3. Vérifier les tables
docker compose exec db psql -U dhr -d dhr -c "\dt"
docker compose exec db psql -U dhr -d dhr -c "\dv"
docker compose exec db psql -U dhr -d dhr -c "\df"

# 4. Vérifier le downgrade (idempotent)
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head

# 5. Vérifier le seed
docker compose exec db psql -U dhr -d dhr -c "SELECT * FROM source;"
```
#### Test de Coherence
```bash
# Vérifier que les modèles se chargent sans erreur
docker compose exec backend python -c "from app.models import Source, Ouvrage, LigneIngeree; print('OK')"

# Vérifier qu'Alembic voit toutes les tables
docker compose exec backend alembic current
# Attendu : 0001_initial (head)

# Vérifier qu'il n'y a pas de dérive entre models.py et la base
docker compose exec backend alembic revision --autogenerate -m "test drift"
# Attendu : aucune migration générée (ou seulement des commentaires)
# Si une migration est générée, inspecte-la : elle ne devrait contenir que des
# différences GIN/GIST ou colonnes générées (que SQLAlchemy ne voit pas).
# Supprime le fichier généré s'il est vide de changements réels.
```

#### Verifier que la Base est intacte
```bash
# Vérifier que les 13 tables existent
docker compose exec db psql -U dhr -d dhr -c "\dt"

# Vérifier que les 3 vues existent
docker compose exec db psql -U dhr -d dhr -c "\dv"

# Vérifier que les 3 fonctions existent
docker compose exec db psql -U dhr -d dhr -c "\df geom_from_latlon"

# Vérifier que les colonnes générées existent
docker compose exec db psql -U dhr -d dhr -c "\d+ localite"
docker compose exec db psql -U dhr -d dhr -c "\d+ ouvrage"
docker compose exec db psql -U dhr -d dhr -c "\d+ ligne_ingeree"

# Vérifier que les index GIN/GIST existent
docker compose exec db psql -U dhr -d dhr -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND indexdef LIKE '%gin%' OR indexdef LIKE '%gist%';"
```