# -*- coding: utf-8 -*-
"""
Step 2: 5) 검수 탭 B열 URL을 읽어 정상/오류 판별 후 C열에 기입, D열에 검수 시각 기입
- 맨 위에서 확인한 Olive Young 정상/오류 구분 방식 사용
  (상품: Product Not Found / not-found 리다이렉트, 기획전: 빈 날짜 패턴)
"""
import os
import re
import sys
import urllib.request
from datetime import datetime
from urllib.parse import urlparse, parse_qs

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 설정 (step1, spreadsheet_connect_test와 동일)
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
REVIEW_SHEET_NAME = "5) 검수"
URL_FIRST_ROW = 3   # B3부터 URL
# 4개 Builder 시트: 랜딩 URL 열 위치가 다름. 각 시트 9행부터 전체 랜딩 점검.
BUILDER_DA_SHEET_NAME = "2) Builder_DA"
BUILDER_DA_URL_COL = 16   # P열 (점검 대상 랜딩 URL)
BUILDER_DA_CHECK_COL = 9   # I열: 오류 시 체크 표시 (체크박스 또는 드롭다운)
BUILDER_DA_DATA_FIRST_ROW = 9
BUILDER_DA_DATA_LAST_ROW = 99999   # 시트 전체 (실제 행 수만큼 처리)
# True면 I열을 체크박스(TRUE/FALSE)로 사용, False면 드롭다운 텍스트 값 사용
BUILDER_DA_USE_CHECKBOX = True
BUILDER_DA_ERROR_CHECK_VALUE = "✓"   # 체크박스 미사용 시 넣을 텍스트 (드롭다운 항목에 맞게 수정)

BUILDER_PMAX_SHEET_NAME = "2) Builder_PMAX"
BUILDER_PMAX_URL_COL = 14   # N열 (랜딩 URL)
BUILDER_PMAX_CHECK_COL = 8   # H열: 오류 시 체크박스
BUILDER_PMAX_DATA_FIRST_ROW = 9
BUILDER_PMAX_DATA_LAST_ROW = 99999

BUILDER_SA_SHEET_NAME = "2) Builder_SA"
BUILDER_SA_URL_COL = 16   # P열 (랜딩 URL)
BUILDER_SA_CHECK_COL = 8   # H열: 오류 시 체크박스
BUILDER_SA_DATA_FIRST_ROW = 9
BUILDER_SA_DATA_LAST_ROW = 99999

BUILDER_CRITEO_SHEET_NAME = "2) Builder_Criteo"
BUILDER_CRITEO_URL_COL = 15   # O열 (랜딩 URL)
BUILDER_CRITEO_CHECK_COL = 8   # H열: 오류 시 체크박스
BUILDER_CRITEO_DATA_FIRST_ROW = 9
BUILDER_CRITEO_DATA_LAST_ROW = 99999

# Google Sheets API batchUpdate 요청 수 제한(약 1000)으로 인해 청크 단위로 전송
BATCH_UPDATE_CHUNK_SIZE = 500

# 테스트용: 환경 변수 STEP2_TEST_LAST_ROW=362 설정 시 4개 Builder 시트 모두 해당 행까지 점검
TEST_LAST_ROW = None
try:
    _env = os.environ.get("STEP2_TEST_LAST_ROW", "")
    if _env.isdigit():
        TEST_LAST_ROW = int(_env)
except Exception:
    pass

# 요청 설정
TIMEOUT_SEC = 8
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://global.oliveyoung.com/",
}
# 오류 판정 기준 (Olive Young)
DEAD_LANDING_KEYWORDS = [
    "This product may be out of stock, discontinued, or the link is incorrect",
    "Product Not Found",
]
# 제미나이 참고: 오류 페이지에 흔한 문구 (대소문자 무시)
# Restock은 정상 페이지 'Restock Notification'과 겹쳐 제외
PRODUCT_ERROR_TEXT_MARKERS = [
    "Sold Out",
    "not exist",
    "not available",
]
# 품절/삭제 페이지 전용 HTML 요소 (페이지 소스 기준)
PRODUCT_ERROR_ELEMENT_MARKERS = [
    "img_product.png",  # 에러 이미지
    'class="error-area"',
    'class="error-icon"',
    "error-not-found",  # <div class="main type-error error-not-found">
    "btn-group-error",  # 오류 페이지 버튼 영역
]
BODY_READ_MAX_BYTES = 350000
EVENT_PLANNING_PATH = "event/planning"
EVENT_EMPTY_DATE_MARKERS = ("~ (KST", "(KST, UTC+9)")
EVENT_HAS_REAL_DATE_PATTERN = re.compile(r"20\d{2}-\d{2}-\d{2}")
PRODUCT_DETAIL_PATH = "product/detail"
PRODUCT_NOT_FOUND_PATH = "product/not-found"
# 카테고리 페이지: 상품 그리드에 'Sold Out' 등이 포함될 수 있어 오류 키워드로 판단하지 않음
CATEGORY_DISPLAY_PATH = "display/category"
# 푸터/회사 소개 등 정상 랜딩 (오류 키워드로 판단하지 않음)
FOOTER_CONTENTS_PATH = "foot-info/footer-contents"
# 상품 없음 시: (1) <title>에 {{product. (2) title이 공통 문구만 (3) 서버가 titleContents 빈 값으로 둠
PRODUCT_UNFILLED_TEMPLATE_MARKER = "{{product."
# 품절/삭제 시 서버가 주는 초기 HTML에 상품명이 없으면 이 hidden이 빈 값으로 옴 (JS 전)
PRODUCT_EMPTY_TITLE_INPUT = 'id="titleContents" value=""'
PRODUCT_EMPTY_TITLE_INPUT_ALT = "id=\"titleContents\" value=''"  # single-quote 변형
PRODUCT_PAGE_GENERIC_TITLE = "OLIVE YOUNG Global | Korea's No. 1 Health & Beauty Store"


def _get_prdt_no_from_url(url):
    """product/detail URL에서 prdtNo 쿼리값 추출. 없으면 None."""
    if not url or PRODUCT_DETAIL_PATH not in url:
        return None
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        vals = qs.get("prdtNo") or qs.get("prdtno")
        if vals and len(vals) > 0 and vals[0].strip():
            return vals[0].strip()
    except Exception:
        pass
    return None


def _url_landing_match_key(url):
    """같은 랜딩페이지면 동일한 키 반환. accParam 등 추가 쿼리는 무시.
    예: ...?plndpNo=1818 과 ...?plndpNo=1818&accParam=170 → 같은 키.
    display/category는 ctgrNo로 구분(ctgrNo 없으면 path만).
    """
    if not url or not (isinstance(url, str) and url.strip()):
        return ""
    try:
        parsed = urlparse(url.strip())
        path = (parsed.path or "").strip().rstrip("/") or "/"
        qs = parse_qs(parsed.query, keep_blank_values=False)
        key_params = {}
        # 상품·기획전·카테고리 각각 구분 (카테고리 URL이 모두 같은 키로 묶이면 정상도 오류로 체크됨)
        for name in ("prdtNo", "plndpNo", "ctgrNo"):
            vals = qs.get(name) or qs.get(name.lower()) or qs.get(name.upper())
            if vals and vals[0].strip():
                key_params[name] = vals[0].strip()
        parts = [path]
        for k in sorted(key_params.keys()):
            parts.append("%s=%s" % (k, key_params[k]))
        return "?".join(parts) if len(parts) > 1 else parts[0]
    except Exception:
        return (url or "").strip()


def _get_title_from_body(body_text):
    """본문에서 <title>...</title> 내용 추출. 없으면 None."""
    if not body_text:
        return None
    start = body_text.find("<title>")
    if start < 0:
        return None
    start += len("<title>")
    end = body_text.find("</title>", start)
    if end < 0:
        return None
    return body_text[start:end].strip()


def _normalize_title(s):
    """비교용: strip + 아포스트로피(U+2019)를 ASCII로."""
    if not s:
        return ""
    return s.strip().replace("\u2019", "'")


def _product_page_title_unfilled(url, body_text):
    """상품 상세 URL인데 (1) <title>에 {{product. (2) 또는 title이 공통 문구만 (3) 또는 titleContents 빈 값이면 True.
    단, 본문에 해당 URL의 prdtNo가 있으면 정상 페이지로 간주(오류 아님)."""
    if not body_text or PRODUCT_DETAIL_PATH not in url:
        return False
    prdt_no = _get_prdt_no_from_url(url)
    # titleContents 빈 값 / 공통 타이틀일 때: 본문에 prdtNo가 있으면 서버가 상품 데이터를 넣은 것 → 정상
    if prdt_no and prdt_no in body_text:
        if PRODUCT_EMPTY_TITLE_INPUT in body_text or PRODUCT_EMPTY_TITLE_INPUT_ALT in body_text:
            return False
        title_content = _get_title_from_body(body_text)
        if title_content and _normalize_title(title_content) == _normalize_title(PRODUCT_PAGE_GENERIC_TITLE):
            return False
    # 서버가 상품 없을 때 주는 초기 HTML: hidden id="titleContents" value="" 또는 value='' 로 옴
    if PRODUCT_EMPTY_TITLE_INPUT in body_text or PRODUCT_EMPTY_TITLE_INPUT_ALT in body_text:
        return True
    title_content = _get_title_from_body(body_text)
    if not title_content:
        return False
    if PRODUCT_UNFILLED_TEMPLATE_MARKER in title_content:
        return True
    if _normalize_title(title_content) == _normalize_title(PRODUCT_PAGE_GENERIC_TITLE):
        return True
    return False


def _body_indicates_dead_landing(body_text):
    if not body_text:
        return False
    for kw in DEAD_LANDING_KEYWORDS:
        if kw in body_text:
            return True
    for marker in PRODUCT_ERROR_ELEMENT_MARKERS:
        if marker in body_text:
            return True
    lower_body = body_text.lower()
    for marker in PRODUCT_ERROR_TEXT_MARKERS:
        if marker.lower() in lower_body:
            return True
    return False


def _event_page_is_ended(body_text):
    if not body_text:
        return False
    pos = -1
    for m in EVENT_EMPTY_DATE_MARKERS:
        i = body_text.find(m)
        if i >= 0 and (pos < 0 or i < pos):
            pos = i
    if pos < 0:
        return False
    window = body_text[max(0, pos - 150) : pos]
    has_real_date = bool(EVENT_HAS_REAL_DATE_PATTERN.search(window))
    return not has_real_date


def check_url(url, cache):
    if url in cache:
        return cache[url]
    try:
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
            code = r.getcode()
            if code < 200 or code >= 400:
                result = "오류"
            else:
                final_url = r.geturl() or ""
                if "not-found" in final_url.lower():
                    result = "오류"
                else:
                    url_lower = (url or "").lower()
                    # 카테고리·푸터 페이지는 본문 읽기 전에 정상 처리
                    if CATEGORY_DISPLAY_PATH in url_lower or FOOTER_CONTENTS_PATH in url_lower:
                        result = "정상"
                    else:
                        body = r.read(BODY_READ_MAX_BYTES)
                        try:
                            text = body.decode("utf-8", errors="ignore")
                        except Exception:
                            text = body.decode("cp949", errors="ignore")
                        if _body_indicates_dead_landing(text):
                            result = "오류"
                        elif PRODUCT_DETAIL_PATH in url and PRODUCT_NOT_FOUND_PATH in text:
                            result = "오류"
                        elif PRODUCT_DETAIL_PATH in url and (
                            PRODUCT_EMPTY_TITLE_INPUT in text or PRODUCT_EMPTY_TITLE_INPUT_ALT in text
                        ):
                            # titleContents 빈 값이어도 본문에 prdtNo가 있으면 정상(상품 데이터 있음)
                            prdt_no = _get_prdt_no_from_url(url)
                            if not prdt_no or prdt_no not in text:
                                result = "오류"
                            else:
                                result = "정상"
                        elif _product_page_title_unfilled(url, text):
                            result = "오류"
                        elif EVENT_PLANNING_PATH in url and _event_page_is_ended(text):
                            result = "오류"
                        else:
                            result = "정상"
    except Exception:
        # 카테고리 URL은 타임아웃 등 일시 오류 시에도 정상으로 간주(DA 시트 오탐 방지)
        url_lower = (url or "").lower()
        if CATEGORY_DISPLAY_PATH in url_lower:
            result = "정상"
        else:
            result = "오류"
    cache[url] = result
    return result


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

    try:
        ws_review = sh.worksheet(REVIEW_SHEET_NAME)
    except Exception as e:
        print('시트 "%s"를 찾을 수 없습니다. %s' % (REVIEW_SHEET_NAME, e))
        sys.exit(1)

    # B열: URL_FIRST_ROW 행부터 끝까지 (B3, B4, ...)
    all_rows = ws_review.get_all_values()
    if len(all_rows) < URL_FIRST_ROW:
        print("5) 검수 시트에 B열 URL이 없습니다. Step 1을 먼저 실행하세요.")
        sys.exit(1)

    # B열 = 인덱스 1, 0-based row = URL_FIRST_ROW - 1 (5) 검수는 전체 URL 기준)
    b_col_idx = 1
    start_idx = URL_FIRST_ROW - 1
    urls = []
    for i in range(start_idx, len(all_rows)):
        row = all_rows[i]
        val = (row[b_col_idx] if b_col_idx < len(row) else "").strip()
        if not val or not (val.startswith("http://") or val.startswith("https://")):
            continue
        urls.append(val)

    if not urls:
        print("5) 검수 B열에 URL이 없습니다. Step 1을 먼저 실행하세요.")
        sys.exit(1)

    if TEST_LAST_ROW:
        print("(4개 Builder 시트 %d행까지 테스트)" % TEST_LAST_ROW)
    print("5) 검수 B열 URL %d개 점검 중..." % len(urls))
    cache = {}
    results = [check_url(url, cache) for url in urls]
    ok_count = sum(1 for r in results if r == "정상")
    err_count = sum(1 for r in results if r == "오류")
    print("정상: %d / 오류: %d" % (ok_count, err_count))

    # C열 URL_FIRST_ROW부터 결과 기입 (C3, C4, ...)
    values = [[r] for r in results]
    ws_review.update(values, "C%d" % URL_FIRST_ROW, value_input_option="USER_ENTERED")
    print('5) 검수 탭 C%d~C%d에 정상/오류 결과를 기입했습니다.' % (URL_FIRST_ROW, URL_FIRST_ROW + len(results) - 1))

    # D2 셀에만 최종 검수 시각 기입 (yy/mm/dd hh:mm)
    inspect_time = datetime.now().strftime("%y/%m/%d %H:%M")
    ws_review.update("D2", [[inspect_time]], value_input_option="USER_ENTERED")
    print('5) 검수 탭 D2에 검수 시각(%s)을 기입했습니다.' % inspect_time)

    # 테스트 시 4개 Builder 시트 마지막 행 제한 (STEP2_TEST_LAST_ROW=362 등)
    da_last = min(BUILDER_DA_DATA_LAST_ROW, TEST_LAST_ROW) if TEST_LAST_ROW else BUILDER_DA_DATA_LAST_ROW
    pmax_last = min(BUILDER_PMAX_DATA_LAST_ROW, TEST_LAST_ROW) if TEST_LAST_ROW else BUILDER_PMAX_DATA_LAST_ROW
    sa_last = min(BUILDER_SA_DATA_LAST_ROW, TEST_LAST_ROW) if TEST_LAST_ROW else BUILDER_SA_DATA_LAST_ROW
    criteo_last = min(BUILDER_CRITEO_DATA_LAST_ROW, TEST_LAST_ROW) if TEST_LAST_ROW else BUILDER_CRITEO_DATA_LAST_ROW

    # 4개 Builder 시트: 랜딩 URL이 있는 행만 체크 해제 후, 오류 행만 체크 (URL 공백 행은 아무것도 입력 안 함)
    _reset_builder_sheet_check_column(sh, BUILDER_DA_SHEET_NAME, BUILDER_DA_URL_COL, BUILDER_DA_CHECK_COL, BUILDER_DA_DATA_FIRST_ROW, da_last)
    _reset_builder_sheet_check_column(sh, BUILDER_PMAX_SHEET_NAME, BUILDER_PMAX_URL_COL, BUILDER_PMAX_CHECK_COL, BUILDER_PMAX_DATA_FIRST_ROW, pmax_last)
    _reset_builder_sheet_check_column(sh, BUILDER_SA_SHEET_NAME, BUILDER_SA_URL_COL, BUILDER_SA_CHECK_COL, BUILDER_SA_DATA_FIRST_ROW, sa_last)
    _reset_builder_sheet_check_column(sh, BUILDER_CRITEO_SHEET_NAME, BUILDER_CRITEO_URL_COL, BUILDER_CRITEO_CHECK_COL, BUILDER_CRITEO_DATA_FIRST_ROW, criteo_last)

    error_urls = [u for u, r in zip(urls, results) if r == "오류"]
    if error_urls:
        _mark_builder_sheet_errors_in_check_column(sh, BUILDER_DA_SHEET_NAME, BUILDER_DA_URL_COL, BUILDER_DA_CHECK_COL, BUILDER_DA_DATA_FIRST_ROW, da_last, error_urls)
        _mark_builder_sheet_errors_in_check_column(sh, BUILDER_PMAX_SHEET_NAME, BUILDER_PMAX_URL_COL, BUILDER_PMAX_CHECK_COL, BUILDER_PMAX_DATA_FIRST_ROW, pmax_last, error_urls)
        _mark_builder_sheet_errors_in_check_column(sh, BUILDER_SA_SHEET_NAME, BUILDER_SA_URL_COL, BUILDER_SA_CHECK_COL, BUILDER_SA_DATA_FIRST_ROW, sa_last, error_urls)
        _mark_builder_sheet_errors_in_check_column(sh, BUILDER_CRITEO_SHEET_NAME, BUILDER_CRITEO_URL_COL, BUILDER_CRITEO_CHECK_COL, BUILDER_CRITEO_DATA_FIRST_ROW, criteo_last, error_urls)
    else:
        print("오류 URL이 없어 Builder 시트 표시를 건너뜁니다.")


def _reset_builder_sheet_check_column(spreadsheet, sheet_name, url_col, check_col, data_first_row, data_last_row):
    """Builder 시트에서 랜딩 URL이 있는 행만 체크 해제. URL 열이 공백인 행은 아무것도 입력하지 않음."""
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except Exception as e:
        print('시트 "%s" 체크 열 초기화 건너뜀. %s' % (sheet_name, e))
        return
    all_rows = ws.get_all_values()
    if len(all_rows) < data_first_row:
        return
    end_row = min(len(all_rows), data_last_row)
    url_col_idx = url_col - 1
    check_col_idx = check_col - 1
    col_letter = chr(64 + check_col)
    false_cell = {"userEnteredValue": {"boolValue": False}}
    requests = []
    for i in range(data_first_row - 1, end_row):
        row = all_rows[i]
        cell_url = (row[url_col_idx] if url_col_idx < len(row) else "").strip()
        if not cell_url or not (cell_url.startswith("http://") or cell_url.startswith("https://")):
            continue  # URL 공백 행은 건드리지 않음
        requests.append({
            "updateCells": {
                "range": {"sheetId": ws.id, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": check_col_idx, "endColumnIndex": check_col_idx + 1},
                "rows": [{"values": [false_cell]}],
                "fields": "userEnteredValue",
            }
        })
    if not requests:
        return
    try:
        if not BUILDER_DA_USE_CHECKBOX:
            empty_cell = {"userEnteredValue": {"stringValue": ""}}
            requests = [{
                "updateCells": {
                    **req["updateCells"],
                    "rows": [{"values": [empty_cell]}],
                }
            } for req in requests]
        for chunk_start in range(0, len(requests), BATCH_UPDATE_CHUNK_SIZE):
            chunk = requests[chunk_start:chunk_start + BATCH_UPDATE_CHUNK_SIZE]
            spreadsheet.batch_update({"requests": chunk})
        print('"%s" %s열 체크 해제 초기화 완료. (URL 있는 행 %d개, 범위: %d~%d행)' % (sheet_name, col_letter, len(requests), data_first_row, end_row))
    except Exception as e:
        print('"%s" 체크 열 초기화 중 오류: %s' % (sheet_name, e))


def _mark_builder_sheet_errors_in_check_column(spreadsheet, sheet_name, url_col, check_col, data_first_row, data_last_row, error_urls):
    """Builder 시트: 오류 URL과 매칭되는 행의 지정 열에 체크 표시. DA=I열, PMAX/SA/Criteo=H열."""
    error_keys = set(_url_landing_match_key(u) for u in error_urls if _url_landing_match_key(u))
    if not error_keys:
        return
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except Exception as e:
        print('시트 "%s" 체크 열 표시 건너뜀. %s' % (sheet_name, e))
        return
    all_rows = ws.get_all_values()
    if len(all_rows) < data_first_row:
        return
    col_idx = url_col - 1
    sheet_id = ws.id
    end_row = min(len(all_rows), data_last_row)
    check_col_idx = check_col - 1  # 0-based
    if BUILDER_DA_USE_CHECKBOX:
        cell_value = {"userEnteredValue": {"boolValue": True}}   # 체크박스 체크
    else:
        cell_value = {"userEnteredValue": {"stringValue": BUILDER_DA_ERROR_CHECK_VALUE}}
    requests = []
    for i in range(data_first_row - 1, end_row):
        row = all_rows[i]
        cell_url = (row[col_idx] if col_idx < len(row) else "").strip()
        if not cell_url or not (cell_url.startswith("http://") or cell_url.startswith("https://")):
            continue
        if _url_landing_match_key(cell_url) not in error_keys:
            continue
        requests.append({
            "updateCells": {
                "range": {"sheetId": sheet_id, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": check_col_idx, "endColumnIndex": check_col_idx + 1},
                "rows": [{"values": [cell_value]}],
                "fields": "userEnteredValue",
            }
        })
    if not requests:
        print('"%s"에서 오류 URL과 매칭되는 행이 없습니다.' % sheet_name)
        return
    try:
        for chunk_start in range(0, len(requests), BATCH_UPDATE_CHUNK_SIZE):
            chunk = requests[chunk_start:chunk_start + BATCH_UPDATE_CHUNK_SIZE]
            spreadsheet.batch_update({"requests": chunk})
        kind = "체크박스" if BUILDER_DA_USE_CHECKBOX else "드롭다운"
        col_letter = chr(64 + check_col)
        print('"%s"에서 오류 랜딩 %d개 행 %s열에 %s 표시했습니다. (점검 범위: %d~%d행)' % (sheet_name, len(requests), col_letter, kind, data_first_row, end_row))
    except Exception as e:
        print('"%s" 체크 열 적용 중 오류: %s' % (sheet_name, e))


def _reset_builder_sheet_text_color(spreadsheet, sheet_name, data_first_row, data_last_row):
    """Builder 시트의 데이터 구간(행) 글자색을 검정으로 초기화. 직전 검수에서 빨간색으로 표기했던 부분을 되돌림."""
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except Exception as e:
        print('시트 "%s" 초기화 건너뜀. %s' % (sheet_name, e))
        return
    all_rows = ws.get_all_values()
    if len(all_rows) < data_first_row:
        return
    end_row = min(len(all_rows), data_last_row)
    start_row_idx = data_first_row - 1  # 0-based
    # A/B/C열은 건드리지 않음. D열(인덱스 3)부터 끝만 검정으로
    try:
        spreadsheet.batch_update({"requests": [{
            "repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": start_row_idx, "endRowIndex": end_row, "startColumnIndex": 3, "endColumnIndex": 26},
                "cell": {"userEnteredFormat": {"textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}}}},
                "fields": "userEnteredFormat.textFormat.foregroundColor",
            }
        }]})
        print('"%s" 직전 검수 표시 초기화(검정) 완료. (범위: %d~%d행, D열~)' % (sheet_name, data_first_row, end_row))
    except Exception as e:
        print('"%s" 초기화 중 오류: %s' % (sheet_name, e))


def _highlight_error_rows_in_builder_sheet(spreadsheet, sheet_name, url_col, data_first_row, data_last_row, error_urls):
    """검수에서 오류로 나온 URL과 같은 랜딩(accParam 등 무시)인 시트의 지정 열 행을 빨간 글씨로 표시."""
    error_keys = set()
    for u in error_urls:
        k = _url_landing_match_key(u)
        if k:
            error_keys.add(k)
    if not error_keys:
        return
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except Exception as e:
        print('시트 "%s"를 찾을 수 없어 빨간글씨 표시를 건너뜁니다. %s' % (sheet_name, e))
        return
    all_rows = ws.get_all_values()
    if len(all_rows) < data_first_row:
        return
    col_idx = url_col - 1  # 0-based
    sheet_id = ws.id
    end_row = min(len(all_rows), data_last_row)
    requests = []
    for i in range(data_first_row - 1, end_row):
        row = all_rows[i]
        cell_url = (row[col_idx] if col_idx < len(row) else "").strip()
        if not cell_url or not (cell_url.startswith("http://") or cell_url.startswith("https://")):
            continue
        key = _url_landing_match_key(cell_url)
        if key not in error_keys:
            continue
        # A/B/C열은 건드리지 않음. D열(인덱스 3)부터 끝만 빨간색
        red_cell = {"userEnteredFormat": {"textFormat": {"foregroundColor": {"red": 1, "green": 0, "blue": 0}}}}
        requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": 3, "endColumnIndex": 26}, "cell": red_cell, "fields": "userEnteredFormat.textFormat.foregroundColor"}})
    if not requests:
        print('"%s"에서 오류 URL과 매칭되는 행이 없습니다.' % sheet_name)
        return
    try:
        spreadsheet.batch_update({"requests": requests})
        print('"%s"에서 오류 랜딩 %d개 행을 빨간 글씨로 표시했습니다. (점검 범위: %d~%d행, D열~)' % (sheet_name, len(requests), data_first_row, end_row))
    except Exception as e:
        print('"%s" 빨간글씨 적용 중 오류: %s' % (sheet_name, e))


if __name__ == "__main__":
    main()
