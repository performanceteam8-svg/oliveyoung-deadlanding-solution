# -*- coding: utf-8 -*-
"""
Step 1: 1) Link 탭 P열·Q열 랜딩 URL 수집 → 중복 제거 → 5) 검수 탭 B열에 기록
"""
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 설정 (spreadsheet_connect_test.py와 동일)
def _default_credentials_path():
    base = os.path.join(os.path.dirname(__file__), "credentials")
    for name in ("service_account.json", "oliveyoung-eu-5e0a60023b49.json", "oliveyoung-eu-oliveyoung-eu-5e0a60023b49.json"):
        path = os.path.join(base, name)
        if os.path.isfile(path):
            return path
    return os.path.join(base, "service_account.json")

CREDENTIALS_PATH = os.environ.get("CREDENTIALS_PATH", _default_credentials_path())
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID",
    "12gg9I032qYNdcE_a0d7RB02eguhLKU7mxiAEkJ47RcU",
)
LINK_SHEET_NAME = "1) Link"
REVIEW_SHEET_NAME = "5) 검수"
DATA_START_ROW = 18   # 17행이 헤더, 18행부터 데이터 (필요 시 수정)
COL_P = 16   # P열 (1-based)
COL_Q = 17   # Q열 (1-based)
# 18행부터 시트 마지막 행까지 읽으므로, P·Q열에 새로 추가된 행도 다음 실행 시 반영됨


def is_url(value):
    v = (value or "").strip()
    if not v or v.lower() == "미운영":
        return False
    return v.startswith("http://") or v.startswith("https://")


def main():
    if not os.path.isfile(CREDENTIALS_PATH):
        print("JSON 키 파일을 찾을 수 없습니다: %s" % CREDENTIALS_PATH)
        sys.exit(1)

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("패키지가 필요합니다: pip install gspread google-auth")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SPREADSHEET_ID)

    # 1) Link 시트
    try:
        ws_link = sh.worksheet(LINK_SHEET_NAME)
    except Exception as e:
        print('시트 "%s"를 찾을 수 없습니다. %s' % (LINK_SHEET_NAME, e))
        sys.exit(1)

    all_rows = ws_link.get_all_values()
    if len(all_rows) < DATA_START_ROW:
        print("Link 시트에 데이터가 없습니다.")
        sys.exit(1)

    start_idx = DATA_START_ROW - 1
    col_p_idx = COL_P - 1
    col_q_idx = COL_Q - 1

    url_set = set()
    # 18행~시트 끝까지 전체 순회 → 새로 추가된 행도 항상 포함
    for i in range(start_idx, len(all_rows)):
        row = all_rows[i]
        p_val = (row[col_p_idx] if col_p_idx < len(row) else "").strip()
        q_val = (row[col_q_idx] if col_q_idx < len(row) else "").strip()
        if is_url(p_val):
            url_set.add(p_val)
        if is_url(q_val):
            url_set.add(q_val)

    urls_sorted = sorted(url_set)
    print("1) Link P열·Q열에서 수집한 URL 수 (중복 제거): %d" % len(urls_sorted))

    # 5) 검수 시트 (없으면 생성)
    try:
        ws_review = sh.worksheet(REVIEW_SHEET_NAME)
    except Exception:
        ws_review = sh.add_worksheet(title=REVIEW_SHEET_NAME, rows=max(500, len(urls_sorted) + 10), cols=10)
        print('시트 "%s"가 없어 새로 만들었습니다.' % REVIEW_SHEET_NAME)

    # B열에 URL만 기록 (B3부터, 한 셀에 하나씩)
    values = [[url] for url in urls_sorted]
    if not values:
        print("기록할 URL이 없습니다.")
        return

    ws_review.update(values, "B3", value_input_option="USER_ENTERED")
    print('5) 검수 탭 B3부터 %d개 URL을 기록했습니다.' % len(urls_sorted))


if __name__ == "__main__":
    main()
