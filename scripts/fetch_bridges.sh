#!/bin/bash
set -euo pipefail

CITY_CODE=${1:-}
PAGE_SIZE=5000
OFFSET=0

if [ -z "$CITY_CODE" ]; then
  echo "使い方: bash scripts/fetch_bridges.sh <市区町村コード>" >&2
  exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)

RAW_DIR="${PROJECT_ROOT}/data/raw"
RAW_FILE="${RAW_DIR}/${CITY_CODE}.json"

mkdir -p "${RAW_DIR}"

# 一時ディレクトリで作業
WORK_DIR=$(mktemp -d "${RAW_DIR}/.fetch-${CITY_CODE}.XXXXXX")
trap 'rm -rf "${WORK_DIR}"' EXIT
WORK_FILE="${WORK_DIR}/combined.json"
PAGE_FILE="${WORK_DIR}/page.json"
MERGED_FILE="${WORK_DIR}/merged.json"

curl -fsS -o "${WORK_FILE}" \
  "https://road-structures-db.mlit.go.jp/xROAD/api/v1/bridges?city=${CITY_CODE}&limit=${PAGE_SIZE}&offset=${OFFSET}"

TOTAL_COUNT=$(jq '.resultset.count' "${WORK_FILE}")
FETCHED_COUNT=$(jq '.result | length' "${WORK_FILE}")

while [ "${FETCHED_COUNT}" -lt "${TOTAL_COUNT}" ]; do
  OFFSET=${FETCHED_COUNT}

  curl -fsS -o "${PAGE_FILE}" \
    "https://road-structures-db.mlit.go.jp/xROAD/api/v1/bridges?city=${CITY_CODE}&limit=${PAGE_SIZE}&offset=${OFFSET}"

  PAGE_COUNT=$(jq '.result | length' "${PAGE_FILE}")

  if [ "${PAGE_COUNT}" -eq 0 ]; then
    echo "データ取得が途中で停止しました: ${FETCHED_COUNT}/${TOTAL_COUNT}件" >&2
    exit 1
  fi

  jq -s '.[0].result += .[1].result | .[0]' \
    "${WORK_FILE}" "${PAGE_FILE}" > "${MERGED_FILE}"

  mv "${MERGED_FILE}" "${WORK_FILE}"

  FETCHED_COUNT=$(jq '.result | length' "${WORK_FILE}")
  echo "取得済: ${FETCHED_COUNT}/${TOTAL_COUNT}件"
done

if [ "${FETCHED_COUNT}" -ne "${TOTAL_COUNT}" ]; then
  echo "取得件数が一致しません: ${FETCHED_COUNT}/${TOTAL_COUNT}件" >&2
  exit 1
fi

jq . "${WORK_FILE}" > "${MERGED_FILE}"
mv "${MERGED_FILE}" "${RAW_FILE}"

echo "取得完了: ${FETCHED_COUNT}件"
