# Step 2 검수 스크립트 — 실행 프롬프트

아래를 복사해 실행 지시용으로 사용하세요.

---

## cmd에서 한 줄로 실행 (Step1 → Step2)

**프로젝트 폴더로 이동한 뒤** 아래 중 하나를 그대로 넣으면 됨.

```cmd
cd c:\Users\MADUP\vibecoding
python step1_collect_urls_to_검수.py && python step2_check_and_fill_c.py
```

- `&&` : step1이 **성공했을 때만** step2 실행 (권장)
- `&` : step1 끝나면 **무조건** step2 실행 (step1 실패해도 step2 돌아감)

Step2만 돌릴 때:

```cmd
cd c:\Users\MADUP\vibecoding
python step2_check_and_fill_c.py
```

---

## 실행 프롬프트 (AI/복사용)

```
vibecoding 프로젝트에서 Step 2 검수를 실행해줘.

1) 프로젝트 루트(c:\Users\MADUP\vibecoding 또는 현재 워크스페이스)로 이동한 뒤
2) Step1 먼저, 이어서 Step2 실행:
   python step1_collect_urls_to_검수.py && python step2_check_and_fill_c.py

또는 Step2만:
   python step2_check_and_fill_c.py

선택 사항:
- 테스트로 N행까지만 돌리려면 실행 전에: set STEP2_TEST_LAST_ROW=362 (Windows)
- 시트/키 경로: CREDENTIALS_PATH, SPREADSHEET_ID 환경 변수

실행 전 확인: credentials 폴더에 서비스 계정 JSON, pip install gspread google-auth
```
