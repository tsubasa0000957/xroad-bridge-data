#!/bin/bash
set -euo pipefail

curl -sS \
  "https://road-structures-db.mlit.go.jp/xROAD/api/v1/bridges?city=112348&limit=170&offset=0" -o yashio.json