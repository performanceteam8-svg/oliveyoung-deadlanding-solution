# -*- coding: utf-8 -*-
"""
특정 URL 응답 본문 확인 (데드랜딩 키워드 검색용)
- 실행: python test_url_response.py
- 92행 예시 URL(plndpNo=1366) 응답에서 'ongoing' 등 검색 결과 출력
"""
import urllib.request
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

URL = "https://global.oliveyoung.com/event/planning?plndpNo=1366&accParam=170"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
READ_BYTES = 400000

def main():
    print("요청 URL:", URL)
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print("상태 코드:", r.getcode())
            print("최종 URL:", r.geturl())
            body = r.read(READ_BYTES)
    except Exception as e:
        print("에러:", e)
        return
    text = body.decode("utf-8", errors="ignore")
    print("본문 길이 (바이트):", len(body))
    print()

    # 검색할 문자열들
    searches = [
        "ongoing",
        "not an ongoing",
        "going on right now",
        "This is not",
        "event has ended",
        "plndpNo",
    ]
    lower = text.lower()
    for s in searches:
        pos = lower.find(s.lower())
        if pos >= 0:
            snippet = text[max(0, pos - 40) : pos + len(s) + 60]
            snippet = snippet.replace("\n", " ").replace("\r", " ")
            print("[발견] %r -> ...%s..." % (s, snippet[:120]))
        else:
            print("[없음] %r" % s)
    print()
    # "ongoing" 주변 500자 저장
    idx = lower.find("ongoing")
    if idx >= 0:
        with open("response_snippet_ongoing.txt", "w", encoding="utf-8") as f:
            f.write(text[max(0, idx - 300) : idx + 500])
        print("'ongoing' 주변 텍스트를 response_snippet_ongoing.txt 에 저장했습니다.")

if __name__ == "__main__":
    main()
