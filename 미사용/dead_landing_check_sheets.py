# -*- coding: utf-8 -*-
"""
데드랜딩 점검 (구글 스프레드시트 API)
- Link 시트에서 E열(영국)·F열(이스라엘) URL 수집 후 중복 제거
- 각 URL 접속 검증 (정상/오류)
- 같은 스프레드시트 안 [URL] 시트에 결과 기록 (없으면 생성)
"""
import os
import re
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 설정: 본인 환경에 맞게 수정
CREDENTIALS_PATH = os.environ.get(
    "CREDENTIALS_PATH",
    os.path.join(os.path.dirname(__file__), "credentials", "service_account.json"),
)
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID",
    "1iZuRoTV25gyAREoQaOY8TlYXfPhQXfFYUbzAzTKM9Og",
)
LINK_SHEET_NAME = "1) Link"
URL_SHEET_NAME = "[URL]"
DATA_START_ROW = 18   # 17행이 헤더, 18행부터 데이터
COL_E = 5             # E열 영국 (1-based)
COL_F = 6             # F열 이스라엘 (1-based)
TIMEOUT_SEC = 8
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# 브라우저처럼 보이게 해서 서버가 302 → not-found 리다이렉트를 주도록 함 (최종 도착 URL 기준 오류 판정)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://global.oliveyoung.com/",
}
# =============================================================================
# 오류 판정 기준 (Olive Young 기준, 정상 페이지 오탐 최소화)
# - 상품: 최종 URL not-found 또는 본문에 not-found 전용 긴 문장만 사용
# - 기획전: 본문 키워드 대신 "빈 날짜 패턴만 있고 실제 날짜 없음"으로 판정
# =============================================================================
#
# [상품 오류] 품절/삭제: 1순위 = 클릭 후 최종 도착 URL이 not-found (서버 302 시 r.geturl()로 감지)
#   - 서버가 302 안 주면: 본문 키워드 또는 본문에 product/not-found 경로로 fallback
#
# [기획전 오류] 종료된 기획전: URL이 event/planning 이고, 본문에 "~ (KST" 있으나
#   "20XX-XX-XX" 형태 실제 날짜가 없을 때만 오류 (JS 팝업 문구는 본문에 없을 수 있어 제외)
#
DEAD_LANDING_KEYWORDS = [
    # 상품 not-found 페이지 전용 (정상 상품 페이지에는 없음)
    "This product may be out of stock, discontinued, or the link is incorrect",
    "Product Not Found",
]
# 제미나이 참고: 오류 페이지 문구 (대소문자 무시). Restock은 정상 쪽 'Restock Notification'과 겹쳐 제외
PRODUCT_ERROR_TEXT_MARKERS = [
    "Sold Out",
    "not exist",
    "not available",
]
# 품절/삭제 페이지 전용 HTML 요소 (페이지 소스 기준)
PRODUCT_ERROR_ELEMENT_MARKERS = [
    "img_product.png",
    'class="error-area"',
    'class="error-icon"',
    "error-not-found",  # <div class="main type-error error-not-found">
    "btn-group-error",  # 오류 페이지 버튼 영역
]
# 본문에서 읽을 최대 바이트
BODY_READ_MAX_BYTES = 350000
# 기획전 오류: 빈 날짜 패턴(종료된 이벤트) 감지용
EVENT_PLANNING_PATH = "event/planning"
EVENT_EMPTY_DATE_MARKERS = ("~ (KST", "(KST, UTC+9)")
EVENT_HAS_REAL_DATE_PATTERN = re.compile(r"20\d{2}-\d{2}-\d{2}")
# 상품 오류: JS/클라이언트 리다이렉트로 not-found 가는 경우 (본문에 경로 포함)
PRODUCT_DETAIL_PATH = "product/detail"
PRODUCT_NOT_FOUND_PATH = "product/not-found"
# 상품 없음 시: (1) <title>에 {{product. (2) title이 공통 문구만 (3) titleContents 빈 값
PRODUCT_UNFILLED_TEMPLATE_MARKER = "{{product."
PRODUCT_PAGE_GENERIC_TITLE = "OLIVE YOUNG Global | Korea's No. 1 Health & Beauty Store"
PRODUCT_EMPTY_TITLE_INPUT = 'id="titleContents" value=""'
PRODUCT_EMPTY_TITLE_INPUT_ALT = "id=\"titleContents\" value=''"


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


def _get_title_from_body(body_text):
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


def is_url(value):
    v = (value or "").strip()
    if not v or v.lower() == "미운영":
        return False
    return v.startswith("http://") or v.startswith("https://")


def _body_indicates_dead_landing(body_text):
    """응답 본문에 상품 not-found 전용 키워드 또는 오류 페이지 전용 요소/문구가 있으면 True."""
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


def _product_page_title_unfilled(url, body_text):
    """상품 상세 URL인데 (1) <title>에 {{product. (2) title이 공통 문구만 (3) titleContents 빈 값이면 True.
    단, 본문에 해당 URL의 prdtNo가 있으면 정상 페이지로 간주(오류 아님)."""
    if not body_text or PRODUCT_DETAIL_PATH not in url:
        return False
    prdt_no = _get_prdt_no_from_url(url)
    if prdt_no and prdt_no in body_text:
        if PRODUCT_EMPTY_TITLE_INPUT in body_text or PRODUCT_EMPTY_TITLE_INPUT_ALT in body_text:
            return False
        title_content = _get_title_from_body(body_text)
        if title_content and _normalize_title(title_content) == _normalize_title(PRODUCT_PAGE_GENERIC_TITLE):
            return False
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


def _event_page_is_ended(body_text):
    """기획전 페이지 본문에 빈 날짜 패턴만 있고, (KST 근처에) 실제 기간(20XX-XX-XX)이 없으면 True.
    푸터/네비 등 다른 영역의 날짜는 제외하기 위해 (KST, UTC+9) 앞 150자만 검사."""
    if not body_text:
        return False
    # "(KST, UTC+9)" 또는 "~ (KST" 위치 찾기
    pos = -1
    for m in EVENT_EMPTY_DATE_MARKERS:
        i = body_text.find(m)
        if i >= 0 and (pos < 0 or i < pos):
            pos = i
    if pos < 0:
        return False
    # 해당 마커 앞 150자 안에만 실제 날짜(20XX-XX-XX) 있는지 확인
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
                # 리다이렉트 후 최종 URL이 not-found 이면 품절/상품없음
                final_url = r.geturl() or ""
                if "not-found" in final_url.lower():
                    result = "오류"
                else:
                    # 2xx/3xx여도 본문 검사: 상품 not-found 문구 또는 기획전 빈 날짜 패턴
                    body = r.read(BODY_READ_MAX_BYTES)
                    try:
                        text = body.decode("utf-8", errors="ignore")
                    except Exception:
                        text = body.decode("cp949", errors="ignore")
                    if _body_indicates_dead_landing(text):
                        result = "오류"
                    elif PRODUCT_DETAIL_PATH in url and PRODUCT_NOT_FOUND_PATH in text:
                        # 상품 상세 요청인데 본문에 not-found 경로 있음 → JS 리다이렉트 등
                        result = "오류"
                    elif PRODUCT_DETAIL_PATH in url and (
                        PRODUCT_EMPTY_TITLE_INPUT in text or PRODUCT_EMPTY_TITLE_INPUT_ALT in text
                    ):
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
        ws_link = sh.worksheet(LINK_SHEET_NAME)
    except gspread.WorksheetNotFound:
        print('시트 "%s"를 찾을 수 없습니다.' % LINK_SHEET_NAME)
        sys.exit(1)

    # E열·F열 데이터 (18행부터)
    all_rows = ws_link.get_all_values()
    if len(all_rows) < DATA_START_ROW:
        print("Link 시트에 데이터가 없습니다.")
        sys.exit(1)

    # 0-based: 데이터 시작 인덱스 = DATA_START_ROW - 1, E=4, F=5
    start_idx = DATA_START_ROW - 1
    col_e_idx = COL_E - 1
    col_f_idx = COL_F - 1

    uk_set = set()
    il_set = set()
    for i in range(start_idx, len(all_rows)):
        row = all_rows[i]
        e_val = (row[col_e_idx] if col_e_idx < len(row) else "").strip()
        f_val = (row[col_f_idx] if col_f_idx < len(row) else "").strip()
        if is_url(e_val):
            uk_set.add(e_val)
        if is_url(f_val):
            il_set.add(f_val)

    uk_urls = sorted(uk_set)
    il_urls = sorted(il_set)
    print("영국(E열) URL 수 (중복 제거): %d" % len(uk_urls))
    print("이스라엘(F열) URL 수 (중복 제거): %d" % len(il_urls))

    cache = {}
    uk_results = [(url, check_url(url, cache)) for url in uk_urls]
    il_results = [(url, check_url(url, cache)) for url in il_urls]

    # [URL] 시트 생성 또는 가져오기
    try:
        ws_url = sh.worksheet(URL_SHEET_NAME)
        ws_url.clear()
    except gspread.WorksheetNotFound:
        ws_url = sh.add_worksheet(title=URL_SHEET_NAME, rows=1000, cols=10)

    # 영국 블록
    out = [["영국", ""], ["URL", "검증결과"]]
    out += [[url, res] for url, res in uk_results]
    out.append([])
    out.append(["이스라엘", ""])
    out.append(["URL", "검증결과"])
    out += [[url, res] for url, res in il_results]

    ws_url.update(out, "A1", value_input_option="USER_ENTERED")
    print('결과를 시트 "[URL]"에 저장했습니다.')
    print("영국: 정상 %d / 오류 %d" % (sum(1 for _, r in uk_results if r == "정상"), sum(1 for _, r in uk_results if r == "오류")))
    print("이스라엘: 정상 %d / 오류 %d" % (sum(1 for _, r in il_results if r == "정상"), sum(1 for _, r in il_results if r == "오류")))


if __name__ == "__main__":
    main()
