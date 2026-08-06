import json
from pathlib import Path
import csv

## このファイルパスを基準にとってる
project_root = Path(__file__).resolve().parent.parent
json_path = project_root / 'data' / 'raw' / 'yashio.json'

## 取りたいデータ 任意の項目名とjsonkeyで対応させる
trg = {
    '施設ID':('shisetsu_id',),
    '橋梁名':('syogen', 'shisetsu', 'meisyou'),
    '路線名':('syogen', 'rosen', 'meisyou'),
    '管理者':('syogen', 'kanrisya', 'meisyou'),
    '管理事務所':('syogen', 'kanrisya', 'jimusyo'),
    '緯度':('syogen', 'ichi', 'ido'),
    '経度':('syogen', 'ichi', 'keido'),
    '架設年度':('syogen','kasetsu_nendo'),
    '橋長':('syogen', 'kyouchou'),
    '幅員':('syogen', 'fukuin'),
    '点検年度':('tenken', 'nendo'),
    '判定区分':('tenken', 'kiroku', 'hantei_kubun'),
    '措置状況':('tenken', 'syuzen', 'sochi_joukyou'),
    '更新日時':('koushin_nichiji',)
}

def load_json(f_path):
    with open(f_path) as json_open:
        source_data = json.load(json_open)
    return source_data

def write_csv(data):
    file_path = project_root / "data" / "processed" / "processed.csv"
    header = list(trg)

    with open(file_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)

def convert_bridge_to_row(bridge):
    row = []
    ## csvの各列について 対応するjsonキーの経路を取得 -> 経路を順に辿る -> rowにappend
    for trg_key in trg:
        curr_val = bridge
        for key in trg[trg_key]:
            curr_val = curr_val[key]
        row.append(curr_val)
    return row

def build_csv_rows(bridges):
    ## 橋梁ごとに行を追加
    rows = []
    for bridge in bridges:
        rows.append(convert_bridge_to_row(bridge))
    return rows


def main():
    source_data = load_json(json_path)['result']
    rows = build_csv_rows(source_data)
    write_csv(rows)

if __name__ == '__main__':
    main()