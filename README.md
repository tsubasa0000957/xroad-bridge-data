# BridgeBase

国土交通省が公開しているオープンデータセット（xROAD）のうち、施設点検データ（橋梁）をAPIから取得し、地図上に一覧表示するプロジェクトです。

## 必要な環境

- Bash
- `curl`
- `jq`
- Python 3
- Webブラウザ

## 使い方

### 1. データを取得する

プロジェクトルートで、取得対象の市区町村コードを引数として指定します。以下を実行すると、`data/raw/<市区町村コード>.json`が出力されます。
橋梁データは5000件ずつ取得され、全体が1つのJSONファイルにまとめられます。

例えば、埼玉県八潮市のデータを取得する場合は以下のとおりです。

```bash
bash scripts/fetch_bridges.sh 112348
```

なお、市区町村コード（全国地方公共団体コード）は総務省が定め公表しているものを用います。
`https://www.soumu.go.jp/denshijiti/code.html`

### 2. データを変換する

プロジェクトルートで以下を実行すると、`data/processed/processed.csv`と`data/processed/processed.geojson`が出力されます。
第一引数には変換するJSONファイルのパスを指定します。

例えば、埼玉県八潮市のデータを変換する場合は以下のとおりです。

```bash
python3 scripts/normalize.py data/raw/112348.json
```

### 3. 地図を表示する

- プロジェクトルートでローカルサーバーを起動

```bash
python3 -m http.server 8000
```

- サーバー起動中にブラウザで `http://localhost:8000/web/` を開く
- ターミナルで `Ctrl + C` で停止

## ディレクトリ構成

```text
.
├── data/ # 未整形・変換後のデータ
│   ├── raw/ # APIから取得したJSON
│   └── processed/ # 整形後のcsv・GeoJSON
├── scripts/ # データ取得・変換スクリプト
└── web/ # 地図表示用フロントエンド
```
