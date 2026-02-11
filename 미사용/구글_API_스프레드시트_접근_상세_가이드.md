# 구글 API로 스프레드시트 접근 — 상세 가이드

스프레드시트 기반 데드랜딩 솔루션을 위해 **Google API**로 스프레드시트에 접근할 때 필요한 설정·인증·코드·할당량·보안까지 한 문서에 정리했습니다.

---

## 목차

1. [필요한 API와 역할](#1-필요한-api와-역할)
2. [인증 방식 선택](#2-인증-방식-선택)
3. [Google Cloud Console 설정 (단계별)](#3-google-cloud-console-설정-단계별)
4. [스코프(Scope)와 권한](#4-스코프scope와-권한)
5. [할당량(Quota)과 비용](#5-할당량quota과-비용)
6. [Python 환경 설정](#6-python-환경-설정)
7. [코드에서 접근 방법](#7-코드에서-접근-방법)
8. [스프레드시트/시트 식별 방법](#8-스프레드시트시트-식별-방법)
9. [보안 및 키 관리](#9-보안-및-키-관리)
10. [에러 코드와 문제 해결](#10-에러-코드와-문제-해결)
11. [데드랜딩 솔루션 적용 시 참고](#11-데드랜딩-솔루션-적용-시-참고)

---

## 1. 필요한 API와 역할

| API | 용도 | 필수 여부 |
|-----|------|-----------|
| **Google Sheets API** | 스프레드시트 셀 읽기·쓰기, 시트 목록·메타데이터 | **필수** |
| **Google Drive API** | 파일 목록 검색, 스프레드시트를 파일명으로 열기 등 | 선택 |

- **데드랜딩 점검만** 할 경우: **Google Sheets API만** 사용하면 됩니다.
- 스프레드시트를 **파일명으로 검색**해서 열거나, Drive 쪽 권한을 다루려면 **Google Drive API**도 활성화해 두는 것이 좋습니다.

**활성화 경로**
- [Google Cloud Console](https://console.cloud.google.com/) → **API 및 서비스** → **라이브러리**
- "Google Sheets API" 검색 → **사용**
- (선택) "Google Drive API" 검색 → **사용**

---

## 2. 인증 방식 선택

스프레드시트에 접근하는 방식은 크게 두 가지입니다.

| 방식 | 설명 | 적합한 경우 |
|------|------|-------------|
| **서비스 계정 (Service Account)** | 봇 전용 계정 + JSON 키. **스프레드시트를 해당 계정 이메일과 공유**해야 함. | **자동화·스크립트·데드랜딩 점검** (사람 로그인 불필요) |
| **OAuth 2.0 (사용자 인증)** | 사용자가 브라우저에서 로그인·동의 후 토큰 발급. | 사용자 본인 시트를 대신 접근할 때, 또는 "내 구글 계정"으로 동작하는 앱 |

**데드랜딩 솔루션(스프레드시트 기반)** 에서는  
→ **서비스 계정**을 쓰는 것을 권장합니다.  
- 한 번 스프레드시트를 서비스 계정 이메일과 공유해 두면, 이후에는 **사람이 로그인하지 않아도** 스크립트만으로 읽기/쓰기가 가능합니다.

---

## 3. Google Cloud Console 설정 (단계별)

### 3.1 Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속 후 로그인.
2. 상단 **프로젝트 선택** → **새 프로젝트**.
3. **프로젝트 이름** 입력 (예: `dead-landing-check`) → **만들기**.
4. 만들어진 프로젝트를 **선택**한 상태로 다음 단계 진행.

---

### 3.2 API 활성화

1. 왼쪽 메뉴 **☰** → **API 및 서비스** → **라이브러리**.
2. **"Google Sheets API"** 검색 → 클릭 → **사용**.
3. (선택) **"Google Drive API"** 검색 → **사용**.

---

### 3.3 OAuth 동의 화면 설정

서비스 계정만 쓸 때도, 프로젝트에서 **OAuth 동의 화면**이 한 번은 설정되어 있어야 할 수 있습니다.  
**내부용(본인/팀만)** 이면 "내부"로 두면 됩니다.

1. **API 및 서비스** → **OAuth 동의 화면** (또는 **Google Auth 플랫폼** → **브랜딩** 등 최신 메뉴명).
2. **User Type**:  
   - **내부**: 같은 Google Workspace 조직만 사용 시.  
   - **외부**: 다른 구글 계정도 사용 시 (테스트 사용자 추가 가능).
3. **앱 정보**:  
   - **앱 이름**: 예) `데드랜딩 점검`  
   - **사용자 지원 이메일**: 본인 이메일  
4. **범위(Scopes)**  
   - 서비스 계정만 쓸 경우 여기서 범위를 안 써도 됩니다.  
   - OAuth 클라이언트를 쓸 경우 나중에 **사용자 인증 정보**에서 클라이언트 생성 시 scope를 지정합니다.
5. **저장** 또는 **다음** → **완료**.

---

### 3.4 서비스 계정 생성 및 JSON 키 발급

1. **API 및 서비스** → **사용자 인증 정보**.
2. **+ 사용자 인증 정보 만들기** → **서비스 계정**.
3. **서비스 계정 이름** (예: `dead-landing-bot`) → **만들기 및 계속**.
4. **역할** (선택):  
   - 비워두거나, **편집자** 등 편한 역할 선택 → **계속** → **완료**.
5. 목록에서 방금 만든 **서비스 계정** 클릭.
6. **키** 탭 → **키 추가** → **새 키 만들기**.
7. **JSON** 선택 → **만들기**.  
   → JSON 파일이 PC에 다운로드됩니다.

**JSON 파일 내용 중 꼭 알아둘 것**
- `client_email`: 서비스 계정 이메일 (예: `xxx@프로젝트ID.iam.gserviceaccount.com`)  
  → **이 이메일을 스프레드시트 "공유"에 편집자로 추가**해야 API로 해당 시트에 접근 가능합니다.
- `private_key`: 비공개 키. **외부에 노출하면 안 됨.**

---

### 3.5 스프레드시트를 서비스 계정과 공유

1. 데드랜딩 점검용 **구글 스프레드시트**를 브라우저에서 연다.
2. 우측 상단 **공유** 클릭.
3. **사용자 또는 그룹 추가**에 위의 **서비스 계정 이메일**(`client_email`)을 붙여넣기.
4. 권한 **편집자** 선택.
5. **전송** (또는 **공유**) 클릭.

이후에는 **해당 스프레드시트 ID**만 알면, 서비스 계정 JSON으로 읽기/쓰기가 가능합니다.

---

## 4. 스코프(Scope)와 권한

Google Sheets API를 부를 때 사용하는 대표 스코프는 다음과 같습니다.

| 스코프 | 의미 |
|--------|------|
| `https://www.googleapis.com/auth/spreadsheets` | 해당 스프레드시트의 **읽기 + 쓰기** (전체 시트) |
| `https://www.googleapis.com/auth/spreadsheets.readonly` | **읽기 전용** |

- 데드랜딩 솔루션은 **URL 읽기 → 점검 → 결과 쓰기**가 필요하므로  
  → **`https://www.googleapis.com/auth/spreadsheets`** (읽기+쓰기)를 사용하면 됩니다.

**gspread** 사용 시  
- `gspread` + 서비스 계정은 보통 위 전체 스코프로 동작합니다.  
- **google-api-python-client**만 쓸 경우, `Credentials` 생성 시 `scopes=[...]`에 위 URL을 넣습니다.

---

## 5. 할당량(Quota)과 비용

- **Google Sheets API**는 **무료 할당량**이 넉넉합니다.
- **일일 읽기/쓰기 요청 수** 등 제한이 있으나, 데드랜딩 점검처럼 수백~수천 URL·시트 정도 규모는 일반적으로 무료 범위 안입니다.
- 정확한 수치는 [Google Sheets API 할당량 문서](https://developers.google.com/sheets/api/limits)에서 확인하는 것이 좋습니다.
- **비용**: 기본 사용량을 넘지 않으면 **과금 없음**. 넘어가면 Cloud Console **결제** 설정에 따라 과금될 수 있으므로, 필요 시 **할당량 알림**을 설정해 두는 것이 좋습니다.

---

## 6. Python 환경 설정

### 6.1 필요한 패키지

**방식 A: gspread (권장 — 사용이 단순함)**

```bash
pip install gspread google-auth
```

- `gspread`: 스프레드시트 열기, 시트 선택, 셀/범위 읽기·쓰기.
- `google-auth`: 서비스 계정 JSON으로 인증.

**방식 B: Google 공식 클라이언트만 사용**

```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

- `google-api-python-client`: Sheets API의 `spreadsheets().values().get()` / `update()` 등 직접 호출.
- OAuth 사용 시 `google-auth-oauthlib` 필요. **서비스 계정만** 쓸 경우 `google-auth`만 있어도 됩니다.

데드랜딩 솔루션은 **gspread + google-auth** 조합을 권장합니다.

---

### 6.2 JSON 키 파일 위치

- 프로젝트 폴더 안 **`credentials/`** 같은 전용 폴더를 두고, 그 안에 JSON 파일을 넣는 것을 권장합니다.
- 예: `vibecoding/credentials/your-service-account.json`
- **`.gitignore`**에 반드시 추가:  
  `credentials/` 또는 `*.json` (credentials 폴더만 쓰면 `credentials/`만 넣어도 됨).

---

## 7. 코드에서 접근 방법

### 7.1 gspread + 서비스 계정 (권장)

```python
import gspread
from google.oauth2.service_account import Credentials

# 서비스 계정으로 인증 (Sheets + Drive scope)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
CREDENTIALS_PATH = "credentials/your-service-account.json"
SPREADSHEET_ID = "1iZuRoTV25gyAREoQaOY8TlYXfPhQXfFYUbzAzTKM9Og"  # URL의 d/.../edit 부분

creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
client = gspread.authorize(creds)

# 스프레드시트 열기
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# 시트 선택 (이름으로)
sheet = spreadsheet.worksheet("1) Link")  # 또는 "[URL]", "Sheet1" 등

# 읽기
all_values = sheet.get_all_values()           # 전체를 리스트
range_values = sheet.get("E18:F100")          # E18:F100 범위
cell_value = sheet.acell("E18").value         # 단일 셀

# 쓰기
sheet.update("V18:W20", [["정상"], ["오류"], ["정상"]])  # 범위
sheet.update_acell("V18", "정상")                         # 단일 셀
```

- **스프레드시트 ID**: 브라우저 URL  
  `https://docs.google.com/spreadsheets/d/여기가_ID/edit...`  
  에서 `여기가_ID` 부분만 복사하면 됩니다.

---

### 7.2 Google API Python Client 직접 사용

```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = "credentials/your-service-account.json"
SPREADSHEET_ID = "1iZuRoTV25gyAREoQaOY8TlYXfPhQXfFYUbzAzTKM9Og"

creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

# 읽기
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="1) Link!E18:F100",
).execute()
values = result.get("values", [])

# 쓰기
sheet.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range="[URL]!V18:W20",
    valueInputOption="USER_ENTERED",
    body={"values": [["정상"], ["오류"], ["정상"]]},
).execute()
```

- **range** 형식: `"시트이름!A1:B10"` 또는 시트 이름에 공백/특수문자가 있으면 그대로 사용 (예: `1) Link!E18:F100`).

---

## 8. 스프레드시트/시트 식별 방법

| 항목 | 얻는 방법 |
|------|-----------|
| **스프레드시트 ID** | URL `https://docs.google.com/spreadsheets/d/{스프레드시트_ID}/edit` 에서 `{스프레드시트_ID}` 부분. |
| **시트(탭) 이름** | 스프레드시트 하단 탭에 표시된 이름 (예: `1) Link`, `[URL]`). API에서 범위 지정 시 `"시트이름!A1:B2"` 형태로 사용. |
| **시트 ID (gid)** | URL에 `#gid=1234567890` 형태로 나오는 숫자. gspread에서는 보통 **시트 이름**으로 지정하는 것이 편합니다. |

---

## 9. 보안 및 키 관리

- **JSON 키 파일**
  - **절대** Git·공개 저장소·스크린샷에 올리지 않기.
  - `.gitignore`에 `credentials/` 또는 해당 JSON 경로 추가.
- **실행 환경**
  - 로컬: 프로젝트 폴더 안 `credentials/` 등에만 두고, 코드에서는 **경로만** 지정 (또는 환경 변수).
  - 서버: 환경 변수로 JSON 경로를 넘기거나, 시크릿 매니저에 JSON 내용을 넣고 코드에서 읽도록 구성.
- **서비스 계정 이메일**
  - 스프레드시트 공유에 필요한 정보일 뿐, 키만큼 민감하지는 않지만, 불필요하게 공개하지 않는 것이 좋습니다.

---

## 10. 에러 코드와 문제 해결

| 현상 | 원인 | 조치 |
|------|------|------|
| **403 Forbidden** | 권한 없음 | 스프레드시트를 서비스 계정 이메일(`client_email`)과 **편집자**로 공유했는지 확인. |
| **404 Not Found** | 스프레드시트/시트를 찾을 수 없음 | 스프레드시트 ID가 URL의 `d/.../edit` 와 일치하는지, 시트 이름(공백·괄호 포함)이 정확한지 확인. |
| **401 Unauthorized** | 인증 실패 | JSON 키 경로·내용이 맞는지, 해당 서비스 계정이 비활성화/삭제되지 않았는지 확인. |
| **429 Too Many Requests** | 할당량 초과 | 요청 횟수 줄이기, 재시도 간격 두기, 필요 시 할당량 상향 요청. |
| **"파일을 찾을 수 없습니다"** | JSON 경로 오류 | `CREDENTIALS_PATH`가 실제 파일 경로와 동일한지 확인 (절대 경로로 테스트해 보기). |
| **"시트를 찾을 수 없습니다"** (gspread) | 시트 이름 불일치 | 탭 이름을 정확히 입력 (예: `1) Link`, `[URL]`). 앞뒤 공백 없이. |

---

## 11. 데드랜딩 솔루션 적용 시 참고

- **읽을 범위**
  - URL이 있는 시트·열 (예: **1) Link** 시트의 E열·F열 등)을 `get_all_values()` 또는 `get("E:F")` 등으로 읽습니다.
- **쓸 범위**
  - 점검 결과를 쓸 시트 (예: **[URL]**)와 열 (예: URL 열 + 검증 결과 열)을 정한 뒤, `update()`로 한 번에 쓰는 것이 할당량·속도 면에서 유리합니다.
- **스프레드시트 ID·시트 이름**
  - 스크립트 상단에 상수로 두고, 환경별로 한 곳만 수정하도록 하면 관리가 쉽습니다.
- **실행 순서**
  1. 서비스 계정 JSON으로 인증  
  2. 스프레드시트 열기 (`open_by_key(SPREADSHEET_ID)`)  
  3. Link 시트에서 URL 목록 읽기  
  4. URL별 데드랜딩 검증 (기획전/제품 페이지 구분 규칙 적용)  
  5. 결과를 [URL] 시트 등에 쓰기  

이 가이드와 기존 **구글_스프레드시트_API_접근_가이드.md**, **API_권한부여_다음_프로세스.md**를 함께 보시면, Google API로 스프레드시트 기반 데드랜딩 솔루션을 끝까지 구성하실 수 있습니다.
