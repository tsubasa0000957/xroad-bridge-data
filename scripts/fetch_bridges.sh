#!/bin/bash
set -euo pipefail

CITY_CODE=${1:-}

if [ -z "$CITY_CODE" ]; then
  echo "使い方: bash scripts/fetch_bridges.sh <市区町村コード>" >&2
  exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

RAW_DIR="${PROJECT_ROOT}/data/raw"
RAW_FILE="${RAW_DIR}/${CITY_CODE}.json"

mkdir -p "${RAW_DIR}"

curl -sSo \
  "${RAW_FILE}" "https://road-structures-db.mlit.go.jp/xROAD/api/v1/bridges?city=${CITY_CODE}&limit=170&offset=0"

jq . "${RAW_FILE}" > "${RAW_DIR}/tmp" \
  && mv "${RAW_DIR}/tmp" "${RAW_FILE}"
