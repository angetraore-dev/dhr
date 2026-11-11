```bash
# Verifier que l'Api tourne
curl.exe -s http://localhost:8000/health | ConvertFrom-Json | Format-List

# API key (lecture) — depuis .env
$API_KEY = (Get-Content .env | Select-String '^API_KEY_READ=').ToString().Split('=')[1]

# JWT (écriture) — généré dans le conteneur
$JWT = docker compose exec -T backend python -c "from app.auth import create_access_token; print(create_access_token('test', 'admin'))"
$JWT = $JWT.Trim()

Write-Host "API_KEY=$API_KEY"
Write-Host "JWT=$JWT"
# Tester les handlers RFC 7807
# 1 — 401 sans API key
curl.exe -s -H "X-API-Key: $API_KEY" http://localhost:8000/v1/sources | ConvertFrom-Json | ConvertTo-Json -Depth 3

# 2 - 404 sur un fichier inexistant
curl.exe -s -H "X-API-Key: $API_KEY" http://localhost:8000/v1/fichiers/9999 | ConvertFrom-Json | Format-List

# 3 - 422 sur une validation Pydantic mode invalide → 422 géré par FastAPI (Literal)
curl.exe -s -H "Authorization: Bearer $JWT" -X POST `
  "http://localhost:8000/v1/fichiers/1/runs?mode=invalide" | ConvertFrom-Json | ConvertTo-Json -Depth 5

# 4 - 200 OK Cas nominal, pour verifier que rien n'est casse
curl.exe -s -H "X-API-Key: $API_KEY" http://localhost:8000/v1/sources | ConvertFrom-Json | ConvertTo-Json -Depth 3

# 5 - Suite des tests `pytest`

# Tous les tests
docker compose exec -T backend pytest -v

# Avec couverture
docker compose exec -T backend pytest --cov=app --cov-report=term-missing

# Un fichier précis
docker compose exec -T backend pytest tests/test_coordonnees.py -v

# Un test précis
docker compose exec -T backend pytest tests/test_ingestion.py::test_detecter_header_row -v


```
> -T est important : sans lui, docker compose exec alloue un TTY et la sortie est polluée par des caractères de contrôle.

### Lint + typecheck (backend)

```bash
docker compose exec -T backend ruff check app
docker compose exec -T backend ruff format --check app
docker compose exec -T backend mypy app/services app/models
```
### RESET COMPLET

```bash
# Redémarrer le backend (recharge le code)
docker compose restart backend

# Logs en direct
docker compose logs -f backend

# Reset DB (perte de données) — si un test a pollué la base
docker compose exec -T db psql -U dhr -d dhr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T backend alembic upgrade head

```