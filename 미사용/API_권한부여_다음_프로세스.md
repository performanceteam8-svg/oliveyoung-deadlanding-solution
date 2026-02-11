# 스프레드시트 권한 부여 후 다음 프로세스

서비스 계정 이메일로 스프레드시트 **편집자** 권한을 부여한 뒤, 코드에서 API로 접근하는 순서입니다.

---

## Step 1. JSON 키 파일 위치 정하기

1. 구글 클라우드에서 **다운로드한 JSON 키 파일**을 프로젝트 폴더 안에 둔다.
2. **권장**: `vibecoding` 폴더 안에 `credentials` 폴더를 만들고, 그 안에 JSON 파일을 넣는다.  
   - 예: `vibecoding/credentials/static-shine-485716-c8-xxxxx.json`
3. **보안**: JSON 키는 Git에 올리지 않는다.  
   - `.gitignore` 파일에 다음 한 줄을 추가한다.  
   - `credentials/`  
   - 또는 `*.json` (credentials 폴더만 쓰면 `credentials/` 가 더 안전함)

---

## Step 2. Python 패키지 설치

터미널(PowerShell 또는 명령 프롬프트)을 열고, 프로젝트 폴더로 이동한 뒤 아래를 실행한다.

```text
C:\Users\MADUP> cd vibecoding
C:\Users\MADUP\vibecoding> pip install gspread google-auth
```

- `gspread`: 구글 스프레드시트 읽기/쓰기
- `google-auth`: 서비스 계정 JSON으로 인증

---

## Step 3. 연결 테스트 (선택)

스프레드시트에 정상 접속하는지 확인하려면, 아래 스크립트를 실행한다.

- 스크립트: **`spreadsheet_connect_test.py`** (아래 내용으로 프로젝트에 생성해 두었음)
- 실행 전: 스크립트 안의 **JSON 파일 경로**와 **스프레드시트 ID**가 본인 환경과 맞는지 확인한다.

```text
C:\Users\MADUP\vibecoding> python spreadsheet_connect_test.py
```

- "연결 성공" 메시지가 나오면, 권한·키·스프레드시트 ID가 올바른 것이다.

### Step 3 상세: 연결 테스트 설명

**1. 이 테스트가 하는 일**

- 서비스 계정 JSON으로 Google에 로그인
- 지정한 **스프레드시트 ID**로 스프레드시트 열기
- **"1) Link"** 시트의 **A1 셀** 한 개만 읽기
- 성공하면 `연결 성공` + A1 값 출력, 실패하면 에러 메시지 출력

즉, **API·권한·스프레드시트 ID·시트 이름**이 모두 맞는지 한 번에 확인하는 용도입니다.

**2. 실행 전에 확인할 것**

| 항목 | 설명 | 확인 방법 |
|------|------|-----------|
| **JSON 키 파일** | 스크립트는 기본적으로 `credentials/service_account.json` 을 찾습니다. | `vibecoding/credentials/` 폴더에 JSON 파일이 있는지 확인. **파일명이 다르면** (예: `my-project-xxx.json`) 아래 3번처럼 경로를 바꾸거나, 파일을 `service_account.json` 으로 복사해 두세요. |
| **스프레드시트 ID** | 접속할 스프레드시트를 구분하는 ID. | 브라우저에서 스프레드시트를 열었을 때 URL이 `https://docs.google.com/spreadsheets/d/여기_ID/edit` 형태라면, **여기_ID** 부분(영문+숫자 긴 문자열)이 스프레드시트 ID입니다. |
| **시트 이름** | 테스트에서 읽을 시트. | 스프레드시트 하단 탭 이름이 **"1) Link"** 인지 확인. (공백, 괄호 포함) 이름이 다르면 스크립트 44번째 줄의 `"1) Link"` 를 실제 탭 이름으로 수정해야 합니다. |

**3. JSON 파일 경로가 다를 때 (파일명이 service_account.json 이 아닐 때)**

방법 A — **스크립트 수정**: `spreadsheet_connect_test.py` 를 열어서 14번째 줄 근처의 기본 경로를 바꿉니다.

```python
# 예: JSON 파일명이 my-project-12345.json 일 때
os.path.join(os.path.dirname(__file__), "credentials", "my-project-12345.json"),
```

방법 B — **환경 변수로 지정** (PowerShell 예시):

```powershell
C:\Users\MADUP\vibecoding> $env:CREDENTIALS_PATH = "C:\Users\MADUP\vibecoding\credentials\my-project-12345.json"
C:\Users\MADUP\vibecoding> python spreadsheet_connect_test.py
```

**4. 스프레드시트 ID가 다를 때**

`spreadsheet_connect_test.py` 를 열어서 16~18번째 줄 근처의 `SPREADSHEET_ID` 기본값을 본인 스프레드시트 ID로 바꿉니다.

```python
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID",
    "여기에_본인_스프레드시트_ID_붙여넣기",
)
```

또는 실행 전에 환경 변수로 지정 (PowerShell):

```powershell
C:\Users\MADUP\vibecoding> $env:SPREADSHEET_ID = "본인_스프레드시트_ID"
C:\Users\MADUP\vibecoding> python spreadsheet_connect_test.py
```

**5. 실행 방법**

1. 터미널(PowerShell 또는 명령 프롬프트)을 연다.
2. 프로젝트 폴더로 이동한다.  
   `C:\Users\MADUP> cd vibecoding`
3. 아래 명령을 실행한다.  
   `C:\Users\MADUP\vibecoding> python spreadsheet_connect_test.py`

**6. 성공했을 때 출력 예시**

```text
연결 성공. 스프레드시트 ID: 1iZuRoTV25gyAREoQaOY8TlYXfPhQXfFYUbzAzTKM9Og
  시트 "1) Link" A1 값: (비어 있음)
```

또는 A1에 값이 있으면 그 값이 출력됩니다. **"연결 성공"** 이 보이면 API·권한·스프레드시트 ID·시트 이름이 모두 정상이라는 뜻입니다.

**7. 실패했을 때 자주 나오는 메시지**

| 메시지 | 원인 | 조치 |
|--------|------|------|
| **JSON 키 파일을 찾을 수 없습니다** | `credentials/service_account.json` 이 없거나 경로가 다름. | JSON 파일을 `credentials/` 에 두고, 파일명을 `service_account.json` 으로 하거나, 위 3번처럼 경로/환경 변수 지정. |
| **403 / 권한이 없습니다** | 스프레드시트를 서비스 계정 이메일과 공유하지 않았거나, 편집자 권한이 아님. | 스프레드시트 **공유**에서 JSON 안의 `client_email` 을 **편집자**로 추가. |
| **404 / 스프레드시트를 찾을 수 없음** | 스프레드시트 ID가 잘못되었거나, 해당 스프레드시트에 서비스 계정이 공유되어 있지 않음. | URL에서 스프레드시트 ID를 다시 복사. 공유 목록에 서비스 계정 이메일이 있는지 확인. |
| **시트를 찾을 수 없습니다** | 시트 이름이 **"1) Link"** 가 아님. | 스크립트 44번째 줄의 시트 이름을 실제 탭 이름과 똑같이 수정. |
| **패키지가 필요합니다** | `gspread` 또는 `google-auth` 가 설치되지 않음. | `pip install gspread google-auth` 실행 후 다시 테스트. |

**8. 정리**

- 연결 테스트는 **데드랜딩 점검 스크립트를 돌리기 전에** 한 번만 해 보면 됩니다.
- **연결 성공**이 나오면 이후 `dead_landing_check_sheets.py` 도 같은 JSON·스프레드시트 ID를 쓰면 됩니다.

---

## Step 4. 데드랜딩 점검 스크립트 실행 (API 버전)

Link 시트에서 E열(영국)·F열(이스라엘) URL을 수집 → 중복 제거 → 점검 → **[URL]** 시트에 결과를 쓰는 스크립트를 실행한다.

- 스크립트: **`dead_landing_check_sheets.py`** (API 사용 버전)
- 실행:

```text
python dead_landing_check_sheets.py
```

- **동작 요약**
  1. 서비스 계정 JSON으로 로그인
  2. 스프레드시트 `1iZuRoTV25gyAREoQaOY8TlYXfPhQXfFYUbzAzTKM9Og` 열기
  3. **1) Link** 시트에서 E열·F열 URL 수집 후 중복 제거
  4. 각 URL 접속 검증 (정상/오류)
  5. **[URL]** 시트가 없으면 생성, 있으면 내용 지우고  
     → 영국 블록(URL + 검증결과), 이스라엘 블록(URL + 검증결과) 기록

- **설정**: 스크립트 상단의 `CREDENTIALS_PATH`, `SPREADSHEET_ID` 를 본인 JSON 경로·스프레드시트 ID에 맞게 수정한다.

---

## 체크리스트

| 단계 | 할 일 | 완료 |
|------|--------|------|
| 1 | JSON 키 파일을 `credentials/` 등 안전한 곳에 두고 `.gitignore`에 추가 | ☐ |
| 2 | `pip install gspread google-auth` 실행 | ☐ |
| 3 | `spreadsheet_connect_test.py` 로 연결 테스트 (선택) | ☐ |
| 4 | `dead_landing_check_sheets.py` 에서 JSON 경로·스프레드시트 ID 확인 후 실행 | ☐ |

---

## 문제 해결

- **"파일을 찾을 수 없습니다"**  
  → `CREDENTIALS_PATH` 에 넣은 JSON 파일 경로가 실제 파일 위치와 같은지 확인.

- **"권한이 없습니다" / 403**  
  → 스프레드시트 공유에서 서비스 계정 이메일을 **편집자**로 추가했는지 다시 확인.  
  → 스프레드시트 ID가 URL의 `d/.../edit` 사이 문자열과 같은지 확인.

- **"시트를 찾을 수 없습니다"**  
  → Link 시트 이름이 **"1) Link"** 인지 확인. (공백·괄호 포함)

이 순서대로 하면 권한 부여 후 API로 스프레드시트를 사용할 수 있다.
