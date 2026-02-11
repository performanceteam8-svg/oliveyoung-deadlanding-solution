# -*- coding: utf-8 -*-
"""
구글 스프레드시트 API 연결 테스트
- 서비스 계정 JSON으로 인증 후 스프레드시트 1셀 읽기
- 권한·키·스프레드시트 ID가 맞으면 "연결 성공" 출력
"""
import os
import sys

# JSON 키 파일 경로 (환경 변수 CREDENTIALS_PATH 또는 아래 기본값)
def _default_credentials_path():
    base = os.path.join(os.path.dirname(__file__), "credentials")
    # 1) 환경 변수 2) service_account.json 3) oliveyoung-eu-5e0a60023b49.json
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

def main():
    if not os.path.isfile(CREDENTIALS_PATH):
        print("JSON 키 파일을 찾을 수 없습니다: %s" % CREDENTIALS_PATH)
        print("  - credentials/ 폴더에 서비스 계정 JSON 파일을 넣고")
        print("  - 파일명을 service_account.json 으로 하거나, CREDENTIALS_PATH 환경 변수로 경로를 지정하세요.")
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
    # "1) Link" 시트에서 A1 한 셀만 읽기
    ws = sh.worksheet("1) Link")
    val = ws.acell("A1").value
    print("연결 성공. 스프레드시트 ID: %s" % SPREADSHEET_ID)
    print('  시트 "1) Link" A1 값: %s' % (val or "(비어 있음)"))

if __name__ == "__main__":
    main()
