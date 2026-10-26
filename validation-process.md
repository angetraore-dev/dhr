
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
```