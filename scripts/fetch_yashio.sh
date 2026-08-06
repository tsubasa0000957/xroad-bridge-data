#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

RAW_DIR="$PROJECT_ROOT/data/raw"

mkdir -p "$RAW_DIR"

curl -sSo \
  "$RAW_DIR/yashio.json" "https://road-structures-db.mlit.go.jp/xROAD/api/v1/bridges?city=112348&limit=170&offset=0"

jq . "$RAW_DIR/yashio.json" > "$RAW_DIR/tmp" \
  && mv "$RAW_DIR/tmp" "$RAW_DIR/yashio.json"