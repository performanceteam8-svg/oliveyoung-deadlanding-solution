# -*- coding: utf-8 -*-
"""
240행 오류 페이지 URL을 step2와 동일한 방식으로 요청해서
서버가 실제로 어떤 HTML을 주는지 확인합니다.
(우리 스크립트는 Elements가 아니라 이 '초기 HTML'만 봅니다.)
"""
import urllib.request

URL = "https://global.oliveyoung.com/product/detail?prdtNo=GA230619395&dataSource=search_result"
TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://global.oliveyoung.com/",
}
BODY_READ_MAX = 350000

DEAD_LANDING_KEYWORDS = [
    "This product may be out of stock, discontinued, or the link is incorrect",
    "Product Not Found",
]
PRODUCT_ERROR_ELEMENT_MARKERS = [
    "img_product.png",
    'class="error-area"',
    'class="error-icon"',
]
PRODUCT_UNFILLED_TEMPLATE_MARKER = "{{product."


def main():
    print("요청 URL:", URL)
    print()
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = r.read(BODY_READ_MAX).decode("utf-8", errors="ignore")
        final_url = r.geturl()
    print("최종 URL:", final_url)
    print("본문 길이(문자):", len(body))
    print()

    # title
    start = body.find("<title>")
    end = body.find("</title>", start) if start >= 0 else -1
    if start >= 0 and end >= 0:
        title = body[start + 7 : end].strip()
        print("<title> 내용:")
        print("  repr:", repr(title))
        print("  {{product. 포함?", PRODUCT_UNFILLED_TEMPLATE_MARKER in title)
    else:
        print("<title> 없음")
    print()

    # 우리가 쓰는 오류 감지용 문자열이 본문에 있는지
    print("=== 오류 감지용 문자열이 본문에 있는지 (step2와 동일 기준) ===")
    for kw in DEAD_LANDING_KEYWORDS:
        found = kw in body
        print("  키워드:", repr(kw[:50]) + ("..." if len(kw) > 50 else ""), "->", "있음" if found else "없음")
    for marker in PRODUCT_ERROR_ELEMENT_MARKERS:
        found = marker in body
        print("  요소:", repr(marker), "->", "있음" if found else "없음")
    print("  title에 {{product.:", PRODUCT_UNFILLED_TEMPLATE_MARKER in (title if start >= 0 and end >= 0 else ""))
    print()

    # 본문 앞 2000자 저장 (나중에 패턴 찾을 때 사용)
    out_file = "debug_error_page_snippet.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(body[:8000])
    print("본문 앞 8000자 저장:", out_file)
    print("  -> 이 파일에서 '오류' 관련 고유 문구를 찾아 step2에 추가하면 됩니다.")


if __name__ == "__main__":
    main()
