# test-b10.ps1 — Vérifie B10 (handlers RFC 7807)
$ErrorActionPreference = "Stop"

$API_KEY = (Get-Content .env | Select-String '^API_KEY_READ=').ToString().Split('=')[1]
$JWT = (docker compose exec -T backend python -c "from app.auth import create_access_token; print(create_access_token('test', 'admin'))").Trim()

Write-Host "`n=== 1. Healthcheck ===" -ForegroundColor Cyan
curl.exe -s http://localhost:8000/health | ConvertFrom-Json | Format-List

Write-Host "`n=== 2. 401 sans API key ===" -ForegroundColor Cyan
$r = curl.exe -s http://localhost:8000/v1/sources | ConvertFrom-Json
if ($r.type -ne "https://api.dhr.local/errors/unauthorized") { throw "FAIL: type=$($r.type)" }
$r | Format-List

Write-Host "`n=== 3. 404 fichier inexistant ===" -ForegroundColor Cyan
$r = curl.exe -s -H "X-API-Key: $API_KEY" http://localhost:8000/v1/fichiers/9999 | ConvertFrom-Json
if ($r.type -ne "https://api.dhr.local/errors/not-found") { throw "FAIL: type=$($r.type)" }
$r | Format-List

Write-Host "`n=== 4. 200 OK sources ===" -ForegroundColor Cyan
$r = curl.exe -s -H "X-API-Key: $API_KEY" http://localhost:8000/v1/sources | ConvertFrom-Json
if ($r.pagination.total -lt 1) { throw "FAIL: total=$($r.pagination.total)" }
Write-Host "OK — $($r.pagination.total) sources"

Write-Host "`n=== 5. pytest ===" -ForegroundColor Cyan
docker compose exec -T backend pytest -q

Write-Host "`n✅ B10 validé." -ForegroundColor Green

# on lance en faisant: powershell -ExecutionPolicy Bypass -File .\test-b10.ps1