# -*- coding: utf-8 -*-
"""
데드랜딩 점검 스크립트
- CSV(1) Link 시트 기준: B열 시작일 90일 이내 행만 검증
- E열/F열 URL 검증 -> V열/W열에 정상/오류 기입
- 결과 CSV 저장 후 실행 결과 요약 출력
"""
import csv
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import sys
import os

# Windows 콘솔 인코딩
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 설정
CSV_PATH = "데드랜딩 솔루션 시트.csv"
OUTPUT_CSV_PATH = "데드랜딩_솔루션_시트_점검결과.csv"
DAYS_THRESHOLD = 90
TIMEOUT_SEC = 8
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# 테스트 시 검증할 최대 행 수 (None이면 전체)
MAX_ROWS_TO_CHECK = None  # 전체 실행 시 None, 빠른 테스트 시 예: 5

# 열 인덱스 (0부터)
COL_B_START = 1   # 시작일 (250101)
COL_E_LINK = 4    # E열 링크
COL_F_LINK = 5    # F열 링크
COL_V_RESULT = 21 # E열 검증 결과
COL_W_RESULT = 22 # F열 검증 결과
HEADER_ROW_INDEX = 16  # 17행이 헤더 (0-based 16)


def parse_start_date(yymmdd_str):
    """B열 '250101' 형식 -> date. 파싱 실패 시 None."""
    s = (yymmdd_str or "").strip()
    if not s or len(s) != 6 or not s.isdigit():
        return None
    try:
        yy = int(s[:2])
        mm = int(s[2:4])
        dd = int(s[4:6])
        year = 2000 + yy if yy < 100 else yy
        return datetime(year, mm, dd).date()
    except (ValueError, TypeError):
        return None


def is_within_last_90_days(d):
    """오늘 기준 90일 이내인지."""
    if d is None:
        return False
    today = datetime.now().date()
    return (today - d).days <= DAYS_THRESHOLD


def parse_min_date(yymmdd_str):
    """'251101' 형식 -> date. 파싱 실패 시 None."""
    return parse_start_date(yymmdd_str)


def is_start_date_on_or_after(d, min_yymmdd):
    """시작일이 min_yymmdd(예: 251101) 이후인지."""
    if d is None:
        return False
    min_d = parse_min_date(min_yymmdd)
    if min_d is None:
        return False
    return d >= min_d


def is_url(value):
    """검증 대상 URL인지 (비어있거나 '미운영'이면 False)."""
    v = (value or "").strip()
    if not v or v.lower() == "미운영":
        return False
    return v.startswith("http://") or v.startswith("https://")


def check_url(url):
    """URL 접근 검증. 정상 -> '정상', 오류 -> '오류'."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
            code = r.getcode()
            if 200 <= code < 400:
                return "정상"
            return "오류"
    except urllib.error.HTTPError as e:
        return "오류"
    except (urllib.error.URLError, OSError, ValueError, Exception):
        return "오류"


def ensure_columns(row, min_len):
    """행이 min_len 개 이상의 열을 갖도록 빈 셀 추가."""
    while len(row) <= min_len:
        row.append("")
    return row


def run(limit=None, since_yymmdd=None, output_suffix=None):
    """
    limit: 검증할 최대 행 수 (None이면 제한 없음)
    since_yymmdd: 이 날짜(YYMMDD) 이후 행만 검증 (예: '251101'). None이면 90일 이내 필터 사용
    output_suffix: 결과 파일명 맨 뒤에 붙일 문자열 (예: '(2차)' -> 점검결과(2차).csv)
    """
    max_rows = limit if limit is not None else MAX_ROWS_TO_CHECK
    out_path = OUTPUT_CSV_PATH
    if output_suffix:
        base, ext = os.path.splitext(OUTPUT_CSV_PATH)
        out_path = base + output_suffix + ext

    if not os.path.exists(CSV_PATH):
        print(f"파일 없음: {CSV_PATH}")
        return

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) <= HEADER_ROW_INDEX + 1:
        print("데이터 행 없음.")
        return

    header = rows[HEADER_ROW_INDEX]
    data_start = HEADER_ROW_INDEX + 1
    today = datetime.now().date()
    use_since_filter = since_yymmdd is not None

    checked_count = 0
    normal_e = 0
    error_e = 0
    normal_f = 0
    error_f = 0
    skipped_no_date = 0
    skipped_out_of_range = 0
    rows_checked = 0

    for i in range(data_start, len(rows)):
        if max_rows is not None and rows_checked >= max_rows:
            break
        row = ensure_columns(rows[i].copy(), max(COL_V_RESULT, COL_W_RESULT))

        # B열 시작일
        start_val = row[COL_B_START] if len(row) > COL_B_START else ""
        start_date = parse_start_date(start_val)
        if start_date is None:
            skipped_no_date += 1
            continue
        if use_since_filter:
            if not is_start_date_on_or_after(start_date, since_yymmdd):
                skipped_out_of_range += 1
                continue
        else:
            if not is_within_last_90_days(start_date):
                skipped_out_of_range += 1
                continue

        rows_checked += 1
        url_e = row[COL_E_LINK].strip() if len(row) > COL_E_LINK else ""
        url_f = row[COL_F_LINK].strip() if len(row) > COL_F_LINK else ""

        # E열 검증
        if is_url(url_e):
            result_e = check_url(url_e)
            row[COL_V_RESULT] = result_e
            checked_count += 1
            if result_e == "정상":
                normal_e += 1
            else:
                error_e += 1
        else:
            row[COL_V_RESULT] = ""  # 미운영/빈칸은 비움

        # F열 검증
        if is_url(url_f):
            result_f = check_url(url_f)
            row[COL_W_RESULT] = result_f
            checked_count += 1
            if result_f == "정상":
                normal_f += 1
            else:
                error_f += 1
        else:
            row[COL_W_RESULT] = ""

        rows[i] = row

    # 결과 CSV 저장
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # 요약 출력
    print("=" * 50)
    print("데드랜딩 점검 결과")
    print("=" * 50)
    if use_since_filter:
        print(f"조건: 시작일이 {since_yymmdd} 이후인 행만 검증")
    else:
        print(f"기준일: {today} / 최근 {DAYS_THRESHOLD}일 이내 행만 검증")
    print(f"시작일 파싱 불가 제외: {skipped_no_date}행")
    print(f"90일 초과 제외: {skipped_out_of_range}행")
    print()
    print("E열(영국) 검증: 정상 %d / 오류 %d" % (normal_e, error_e))
    print("F열(이스라엘) 검증: 정상 %d / 오류 %d" % (normal_f, error_f))
    print("총 검증 URL 수: %d" % checked_count)
    print()
    print("결과 저장: %s" % out_path)
    print("")
    print("CSV에서 결과 보는 방법:")
    print("  - 엑셀/구글 시트에서 '%s' 파일을 열면 됩니다." % out_path)
    print("  - V열 = E열(영국) 링크 검증 결과 (정상/오류)")
    print("  - W열 = F열(이스라엘) 링크 검증 결과 (정상/오류)")
    print("  - 미운영·빈 링크는 V/W에 빈칸으로 둡니다.")
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="데드랜딩 점검 (E/F열 -> V/W열)")
    parser.add_argument("--limit", type=int, default=None, help="검증할 최대 행 수 (기본: 전체)")
    parser.add_argument("--since", type=str, default=None, metavar="YYMMDD", help="이 날짜 이후 행만 검증 (예: 251101)")
    parser.add_argument("--suffix", type=str, default=None, metavar="STR", help="결과 파일명 맨 뒤에 붙일 문자열 (예: '(2차)')")
    args = parser.parse_args()
    if args.limit is not None:
        print("(테스트 모드: 최대 %d행만 검증)\n" % args.limit)
    if args.since:
        print("(시작일 %s 이후 행만 검증)\n" % args.since)
    run(limit=args.limit, since_yymmdd=args.since, output_suffix=args.suffix)
