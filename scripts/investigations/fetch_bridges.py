import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

PAGE_SIZE = 5000
BRIDGES_API_URL = "https://road-structures-db.mlit.go.jp/xROAD/api/v1/bridges"
# xROAD APIの仕様上、エンドポイント名は "lastest"
BRIDGES_API_ENDPOINTS = {
    "all": BRIDGES_API_URL,
    "lastest": f"{BRIDGES_API_URL}/lastest",
}

INVESTIGATION_DATA_DIR = Path("data/26_investigate")
MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def validate_prefecture_code(value):
    if len(value) != 2:
        raise argparse.ArgumentTypeError(
            "都道府県コードは2桁で入力してください"
        )

    elif not value.isascii() or not value.isdigit():
        raise argparse.ArgumentTypeError(
            "都道府県コードは半角数字で入力してください"
        )

    elif not 1 <= int(value) <= 47:
        raise argparse.ArgumentTypeError(
            "都道府県コードは01～47で入力してください"
        )
    return value


def validate_municipality_code(value):
    if len(value) != 6:
        raise argparse.ArgumentTypeError(
            "市区町村コードは6桁で入力してください"
        )

    elif not value.isascii() or not value.isdigit():
        raise argparse.ArgumentTypeError(
            "市区町村コードは半角数字で入力してください"
        )

    # 市区町村コードに含まれる都道府県コード部分も検証する
    try:
        validate_prefecture_code(value[:2])
    except argparse.ArgumentTypeError:
        raise argparse.ArgumentTypeError(
            "市区町村コードの形式が正しくありません"
        )

    # チェックディジットを検証
    weighted_num = 0
    for i in range(5):
        weighted_num += int(value[i]) * (6 - i)
    check_digit = (11 - (weighted_num % 11)) % 10

    if not check_digit == int(value[5]):
        raise argparse.ArgumentTypeError(
            "市区町村コードの形式が正しくありません"
        )
    return value


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-p",
        "--prefecture",
        type=validate_prefecture_code
    )
    group.add_argument(
        "-m",
        "--municipality",
        type=validate_municipality_code
    )
    group.add_argument("-n", "--nationwide", action="store_true")

    args = parser.parse_args()
    return args


def extract_area(
        args: argparse.Namespace,
    ) -> tuple[str, str | None]:
    d = vars(args).items()
    for attribute_name, value in d:
        if value is None or value is False:
            continue

        if attribute_name == "nationwide":
            return attribute_name, None

        return attribute_name, value
    raise RuntimeError("取得範囲を特定できません")


def build_query_string(
        area_scale: str,
        area_code: str | None,
        offset: int
    ) -> dict[str, int | str]:
    params: dict[str, int | str] = {
        "limit": PAGE_SIZE,
        "offset": offset,
    }

    if area_scale == "prefecture":
        if area_code is None:
            raise RuntimeError("都道府県コードがありません")

        params["pref"] = area_code

    elif area_scale == "municipality":
        if area_code is None:
            raise RuntimeError("市区町村コードがありません")

        params["city"] = area_code

    return params


def fetch_page(endpoint_url: str, query_params: dict) -> dict:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(endpoint_url, params=query_params, timeout=30)
            response.raise_for_status()
            page_data = response.json()

            return page_data

        except (requests.Timeout, requests.ConnectionError) as error:
            if attempt == MAX_ATTEMPTS:
                raise

            wait_seconds = 2 ** (attempt - 1)

            logging.warning(
                "通信エラーのため再試行します: "
                "attempt=%d/%d, wait=%d秒, error=%s",
                attempt,
                MAX_ATTEMPTS,
                wait_seconds,
                error,
            )

            time.sleep(wait_seconds)

        except requests.HTTPError as error:
            if (
                response.status_code not in RETRYABLE_STATUS_CODES
                or attempt == MAX_ATTEMPTS
            ):
                raise

            wait_seconds = 2 ** (attempt - 1)

            logging.warning(
                "HTTPエラーのため再試行します: "
                "status=%d, attempt=%d/%d, wait=%d秒, error=%s",
                response.status_code,
                attempt,
                MAX_ATTEMPTS,
                wait_seconds,
                error,
            )

            time.sleep(wait_seconds)

    raise RuntimeError("ページ取得の試行が実行されませんでした")


def fetch_all_pages(
        endpoint_name: str,
        endpoint_url: str,
        area_scale: str,
        area_code: str | None,
        output_path: Path,
    ) -> None:
    offset = 0
    downloaded_count = 0
    expected_total_count: int | None = None

    # 全件取得に成功するまで正式ファイルは置き換えない
    temporary_output_path = output_path.with_name(f"{output_path.name}.tmp")

    logging.info(
        "[%s] エンドポイント取得開始: output=%s",
        endpoint_name,
        output_path,
    )

    while True:
        query_string = build_query_string(area_scale, area_code, offset)

        page = fetch_page(endpoint_url, query_string)

        is_error = page["resultset"]["is_error"]

        if is_error is not False:
            raise RuntimeError(
                f"[{endpoint_name}] APIがエラーを返しました: "
                f"is_error={is_error!r}, offset={offset}"
            )

        page_results: list = page["result"]

        if not isinstance(page_results, list):
            raise RuntimeError(
                f"[{endpoint_name}] resultがリストではありません: "
                f"type={type(page_results).__name__}"
            )

        with temporary_output_path.open("a", encoding="utf-8") as output_file:
            for record in page_results:
                json.dump(record, output_file, ensure_ascii=False)
                output_file.write("\n")

        downloaded_count += len(page_results)

        # 初回取得時の総件数を基準にし、途中取得で変化した場合は停止する
        reported_total_count = page["resultset"]["count"]
        if not isinstance(reported_total_count, int):
            raise RuntimeError(
                f"[{endpoint_name}] resultset.countが整数ではありません: "
                f"value={reported_total_count!r}"
            )

        if expected_total_count is None:
            expected_total_count = reported_total_count

        elif reported_total_count != expected_total_count:
            raise RuntimeError(
                f"[{endpoint_name}] 取得途中で総件数が変化しました: "
                f"expected={expected_total_count}, reported={reported_total_count}, offset={offset}"
            )

        logging.info(
            "[%s] ページ取得完了: offset=%d, page_count=%d, downloaded=%d, total=%d",
            endpoint_name,
            offset,
            len(page_results),
            downloaded_count,
            expected_total_count,
        )

        if downloaded_count == expected_total_count:
            break

        elif downloaded_count > expected_total_count:
            raise RuntimeError(
                f"[{endpoint_name}] 取得件数が総件数を超えました: "
                f"expected={expected_total_count}, downloaded={downloaded_count}, offset={offset}"
            )

        elif not page_results:
            raise RuntimeError(
                f"[{endpoint_name}] 未完了なのに空ページが返りました: "
                f"expected={expected_total_count}, downloaded={downloaded_count}, offset={offset}"
            )

        offset += PAGE_SIZE

    temporary_output_path.replace(output_path)

    logging.info(
        "[%s] エンドポイント取得完了: downloaded=%d, output=%s",
        endpoint_name,
        downloaded_count,
        output_path,
    )


def main():
    args = parse_args()

    area_scale, area_code = extract_area(args)

    if area_code is None:
        area_identifier = area_scale
    else:
        area_identifier = f"{area_scale}_{area_code}"

    # logger初期設定
    acquired_at = datetime.now().astimezone()
    run_timestamp = acquired_at.strftime("%Y%m%dT%H%M%S%z")

    run_dir = INVESTIGATION_DATA_DIR / f"{run_timestamp}_{area_identifier}"
    run_dir.mkdir(parents=True, exist_ok=False)

    log_path = run_dir / "fetch.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ]
    )

    logging.info(
        "取得開始: acquired_at=%s, area=%s, page_size=%d",
        acquired_at.isoformat(),
        area_identifier,
        PAGE_SIZE,
    )

    for endpoint_name, endpoint_url in BRIDGES_API_ENDPOINTS.items():
        output_path = run_dir / f"{endpoint_name}.jsonl"

        fetch_all_pages(
            endpoint_name,
            endpoint_url,
            area_scale,
            area_code,
            output_path
        )

    logging.info(
        "取得完了: area=%s, output_dir=%s",
        area_identifier,
        run_dir,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("取得処理が異常終了しました")
        raise