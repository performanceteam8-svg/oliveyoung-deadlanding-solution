# -*- coding: utf-8 -*-
"""
데드랜딩 점검 (중복 제거 방식)
- Link 탭(CSV)에서 영국(E열)·이스라엘(F열) URL을 각각 모두 수집
- 중복 제거 후 오류 점검
- 결과를 새 시트(CSV)로 저장: 영국 블록 | 이스라엘 블록
"""
import csv
import urllib.request
import urllib.error
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CSV_PATH = "데드랜딩 솔루션 시트.csv"
OUTPUT_CSV_PATH = "데드랜딩_링크_점검결과_중복제거.csv"
TIMEOUT_SEC = 8
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

COL_E_LINK = 4   # E열 영국
COL_F_LINK = 5   # F열 이스라엘
HEADER_ROW_INDEX = 16  # 17행이 헤더 (0-based)


def is_url(value):
    v = (value or "").strip()
    if not v or v.lower() == "미운영":
        return False
    return v.startswith("http://") or v.startswith("https://")


def check_url(url, cache):
    """URL 검증. cache에 결과 저장해 동일 URL 재요청 방지."""
    if url in cache:
        return cache[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
            code = r.getcode()
            result = "정상" if 200 <= code < 400 else "오류"
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError, Exception):
        result = "오류"
    cache[url] = result
    return result


def collect_unique_urls(rows, col_index):
    """해당 열에서 URL만 수집해 중복 제거 후 리스트 반환."""
    data_start = HEADER_ROW_INDEX + 1
    seen = set()
    urls = []
    for i in range(data_start, len(rows)):
        row = rows[i]
        if col_index >= len(row):
            continue
        val = (row[col_index] or "").strip()
        if not is_url(val):
            continue
        if val in seen:
            continue
        seen.add(val)
        urls.append(val)
    return urls


def run(output_suffix=None):
    out_path = OUTPUT_CSV_PATH
    if output_suffix:
        base, ext = os.path.splitext(OUTPUT_CSV_PATH)
        out_path = base + output_suffix + ext

    if not os.path.exists(CSV_PATH):
        print("파일 없음: %s" % CSV_PATH)
        return

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if len(rows) <= HEADER_ROW_INDEX + 1:
        print("데이터 행 없음.")
        return

    # 영국(E열)·이스라엘(F열) URL 수집 (중복 제거)
    uk_urls = collect_unique_urls(rows, COL_E_LINK)
    il_urls = collect_unique_urls(rows, COL_F_LINK)

    print("=" * 50)
    print("데드랜딩 점검 (중복 제거)")
    print("=" * 50)
    print("영국(E열) 수집 URL 수: %d (중복 제거 후)" % len(uk_urls))
    print("이스라엘(F열) 수집 URL 수: %d (중복 제거 후)" % len(il_urls))
    print()

    cache = {}
    uk_results = []
    for url in uk_urls:
        result = check_url(url, cache)
        uk_results.append((url, result))
        print("  [영국] %s -> %s" % (url[:60] + "..." if len(url) > 60 else url, result))

    il_results = []
    for url in il_urls:
        result = check_url(url, cache)
        il_results.append((url, result))
        print("  [이스라엘] %s -> %s" % (url[:60] + "..." if len(url) > 60 else url, result))

    # 새 시트(CSV) 형태로 저장: 영국 블록 + 이스라엘 블록
    out_rows = []
    out_rows.append(["영국", ""])
    out_rows.append(["URL", "검증결과"])
    for url, res in uk_results:
        out_rows.append([url, res])
    out_rows.append([])  # 빈 행
    out_rows.append(["이스라엘", ""])
    out_rows.append(["URL", "검증결과"])
    for url, res in il_results:
        out_rows.append([url, res])

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(out_rows)

    uk_ok = sum(1 for _, r in uk_results if r == "정상")
    uk_err = sum(1 for _, r in uk_results if r == "오류")
    il_ok = sum(1 for _, r in il_results if r == "정상")
    il_err = sum(1 for _, r in il_results if r == "오류")

    print()
    print("=" * 50)
    print("결과 요약")
    print("=" * 50)
    print("영국: 정상 %d / 오류 %d" % (uk_ok, uk_err))
    print("이스라엘: 정상 %d / 오류 %d" % (il_ok, il_err))
    print("결과 저장: %s" % out_path)
    print("(엑셀/구글 시트에서 열면 영국·이스라엘 각각 URL 목록과 검증결과를 볼 수 있습니다)")
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Link 탭 URL 수집 후 중복 제거하여 점검, 새 시트(CSV)로 저장")
    p.add_argument("--suffix", type=str, default=None, metavar="STR", help='결과 파일명 맨 뒤에 붙일 문자열 (예: "(2차)")')
    args = p.parse_args()
    run(output_suffix=args.suffix)
