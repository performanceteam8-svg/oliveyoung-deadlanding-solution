# -*- coding: utf-8 -*-
"""오류 페이지(GA230619395) 실제 응답의 title 확인."""
import urllib.request

url = "https://global.oliveyoung.com/product/detail?prdtNo=GA230619395&dataSource=search_result"
req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://global.oliveyoung.com/",
    },
)
with urllib.request.urlopen(req, timeout=10) as r:
    body = r.read(200000).decode("utf-8", errors="ignore")

s = body.find("<title>")
e = body.find("</title>", s)
if s >= 0 and e >= 0:
    title = body[s + 7 : e].strip()
    print("TITLE repr:", repr(title))
    print("TITLE len:", len(title))
    print("Contains {{product.:", "{{product." in title)

generic = "OLIVE YOUNG Global | Korea's No. 1 Health & Beauty Store"
print("Equal to constant:", title == generic)
print("Constant repr:", repr(generic))

# Normalize: strip + replace fancy apostrophe
norm = title.strip().replace("\u2019", "'")
norm_generic = generic.replace("\u2019", "'")
print("After norm, equal:", norm == norm_generic)
