# 1. Étape préliminaire : Charger le référentiel des localités de CI
docker compose exec backend python -u /app/scripts/import_referentiels.py /app/tests/fixtures/fichier1.xlsx  2>&1

# 2. Étape Ingestion brute : Lire le classeur d'ouvrages hydrauliques
docker compose exec backend python -u /app/scripts/test_ingestion_reelle.py /app/tests/fixtures/fichier1.xlsx  2>&1

# 3. Étape Rapprochement : Associer les lignes aux localités (Utilisez l'id_run généré par l'étape 2, ex: 1)
docker compose exec backend python -u /app/scripts/test_rapprochement.py <id_run>

# 4. Étape Consolidation : Fusionner et créer les ouvrages uniques finaux
docker compose exec backend python -u /app/scripts/test_consolidation.py <id_run>
