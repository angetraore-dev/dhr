#!/bin/bash
set -e
set -u

function create_user_and_database() {
    local database=$1
    echo "  Creating database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

# Crée la base de test si elle est spécifiée
if [ ! -z "${POSTGRES_TEST_DB:-}" ]; then
    create_user_and_database "$POSTGRES_TEST_DB"
fi
