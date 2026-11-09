#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-backup.sql}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-supply_chain}"

echo "Creating PostgreSQL backup to ${OUTPUT_FILE} ..."
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > "${OUTPUT_FILE}"
echo "Backup completed: ${OUTPUT_FILE}"
