#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/db_restore.sh <backup.sql>"
  exit 1
fi

INPUT_FILE="$1"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-supply_chain}"

if [[ ! -f "${INPUT_FILE}" ]]; then
  echo "Input file not found: ${INPUT_FILE}"
  exit 1
fi

echo "Restoring PostgreSQL backup from ${INPUT_FILE} ..."
docker compose exec -T postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "${INPUT_FILE}"
echo "Restore completed."
