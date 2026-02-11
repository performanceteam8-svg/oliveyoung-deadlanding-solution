# -*- coding: utf-8 -*-
"""
예시 URL 7개만 검증 (오류/정상 판정 확인용)
- 스프레드시트/API 없이 check_url 로직만 실행
- 기대: 정상 5개, 오류 2개
"""
import sys
import os

# 프로젝트 루트에서 dead_landing_check_sheets 의 check_url 사용
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dead_landing_check_sheets import check_url

EXAMPLES = [
    ("정상", "https://global.oliveyoung.com/"),
    ("정상", "https://global.oliveyoung.com/display/category?ctgrNo=1000000011"),
    ("정상", "https://global.oliveyoung.com/display/page/brand-page?brandNo=B00048"),
    ("정상", "https://global.oliveyoung.com/product/detail?prdtNo=GA230217651"),
    ("정상", "https://global.oliveyoung.com/event/planning?plndpNo=2024&accParam=170"),
    ("오류", "https://global.oliveyoung.com/product/detail?prdtNo=GA240121955"),
    ("오류", "https://global.oliveyoung.com/event/planning?plndpNo=1574&accParam=170"),
]

def main():
    print("예시 URL 검증 (기대: 정상 5개 → 정상, 오류 2개 → 오류)\n")
    cache = {}
    ok = 0
    for expected, url in EXAMPLES:
        result = check_url(url, cache)
        match = "OK" if result == expected else "FAIL"
        if result == expected:
            ok += 1
        print("%s  %s  →  %s  (기대: %s)" % (match, result, url[:60] + "..." if len(url) > 60 else url, expected))
    print("\n총 %d/%d 일치" % (ok, len(EXAMPLES)))
    if ok < len(EXAMPLES):
        sys.exit(1)

if __name__ == "__main__":
    main()
