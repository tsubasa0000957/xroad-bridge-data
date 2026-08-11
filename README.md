# BridgeBase

国土交通省が公開しているオープンデータセット（xROAD）のうち、施設点検データ（橋梁）をAPIから取得し、地図上に一覧表示するプロジェクトです。
現在は埼玉県八潮市のデータを対象としています。

## 必要な環境

- Bash
- `curl`
- `jq`
- Python 3
- Webブラウザ

## 使い方

### 1. データを取得する

プロジェクトルートで以下を実行すると、`data/raw/yashio.json`が出力されます。

```bash
bash scripts/fetch_yashio.sh
```

### 2. データを変換する

プロジェクトルートで以下を実行すると、`data/processed/processed.csv`と`data/processed/processed.geojson`が出力されます。

```bash
python3 scripts/normalize.py
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
