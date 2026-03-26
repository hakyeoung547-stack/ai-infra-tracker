# API 완전 입문 가이드

> 처음 API를 배우는 사람을 위한 쉬운 설명.
> "API가 뭔지 모르겠다"에서 "직접 데이터를 받아올 수 있다"까지.

---

## 1. API란 무엇인가

### 한 줄 정의

> **API** = 프로그램끼리 대화하는 방법

### 쉬운 비유로 이해하기

식당을 생각해보자.

```
손님 (나의 코드)
  ↓  "스테이크 주세요" (요청)
웨이터 (API)
  ↓  주방으로 전달
주방 (서버/데이터베이스)
  ↓  음식 완성
웨이터 (API)
  ↓  "스테이크 나왔습니다" (응답)
손님 (나의 코드)
```

- 나는 주방 안이 어떻게 돌아가는지 몰라도 된다
- 웨이터(API)에게 원하는 걸 말하면 가져다준다
- API는 그 **정해진 주문 방식**이다

### API가 왜 필요한가

| 상황 | API 없이 | API 있으면 |
|------|---------|-----------|
| 지도 기능 구현 | 직접 지도 데이터베이스 구축 | 카카오맵 API 호출 한 줄 |
| 결제 기능 구현 | 직접 카드사와 계약 + 보안 시스템 구축 | 카카오페이 API 연동 |
| 날씨 정보 표시 | 직접 기상 데이터 수집 | 기상청 API 호출 |
| 주가 데이터 수집 | 증권사 서버에 직접 접속 | yfinance API 한 줄 |

---

## 2. HTTP — 인터넷에서 대화하는 규칙

### 기본 개념

API는 대부분 **HTTP**라는 규칙으로 동작한다.
브라우저에서 웹사이트를 열 때도 HTTP를 사용한다.

**HTTP 통신의 흐름:**

```
나 (클라이언트)            서버
    |                       |
    |── "이 데이터 줘" ────→|   요청 (Request)
    |                       |
    |←── "여기 있어" ───────|   응답 (Response)
    |                       |
```

### 요청(Request)의 구조

```
GET /api/stock/NVDA HTTP/1.1          ← 요청 라인 (무엇을, 어디서)
Host: api.example.com                  ← 헤더 (추가 정보들)
Authorization: Bearer abc123           ← 헤더 (인증 정보)
Content-Type: application/json         ← 헤더 (데이터 형식)
                                       ← 빈 줄 (헤더 끝)
{"period": "3m"}                       ← 바디 (실제 데이터, POST일 때)
```

### 응답(Response)의 구조

```
HTTP/1.1 200 OK                        ← 상태 라인 (잘 됐나요?)
Content-Type: application/json         ← 헤더

{"ticker": "NVDA", "price": 875.4}    ← 바디 (실제 데이터)
```

### HTTP 상태 코드 — 숫자로 결과를 알려준다

| 코드 | 의미 | 비유 |
|------|------|------|
| **200** OK | 성공 | "네, 여기 있습니다" |
| **201** Created | 생성 성공 | "새로 만들었습니다" |
| **400** Bad Request | 잘못된 요청 | "무슨 말인지 모르겠어요" |
| **401** Unauthorized | 인증 실패 | "신분증이 없으시네요" |
| **403** Forbidden | 접근 금지 | "여긴 들어오시면 안 돼요" |
| **404** Not Found | 없음 | "그런 거 없어요" |
| **429** Too Many Requests | 요청 과다 | "너무 자주 오시네요. 잠깐만요" |
| **500** Server Error | 서버 오류 | "저희 쪽에서 실수했어요" |

> **팁**: 200번대 = 성공, 400번대 = 내 잘못, 500번대 = 서버 잘못

### 자주 보는 헤더 필드

| 헤더 | 의미 | 예시 |
|------|------|------|
| `Host` | 어느 서버로 보낼지 | `api.naver.com` |
| `Authorization` | 내가 누구인지 (인증) | `Bearer API키값` |
| `Content-Type` | 데이터 형식 | `application/json` |
| `User-Agent` | 어떤 프로그램이 보내는지 | `Mozilla/5.0...` |

---

## 3. HTTP 메서드 — 어떤 행동을 할지 알려준다

### 4가지 기본 동작

| 메서드 | 행동 | 비유 | 데이터 위치 |
|--------|------|------|-------------|
| **GET** | 가져오기 | 도서관에서 책 빌리기 | URL에 포함 |
| **POST** | 만들기/보내기 | 도서관에 새 책 기증하기 | Body에 포함 |
| **PUT** | 전체 수정 | 책 전체를 새 버전으로 교체 | Body에 포함 |
| **DELETE** | 삭제 | 책 폐기 | URL에 포함 |

### Python 예시

```python
import requests

# GET — 데이터 조회
response = requests.get("https://api.example.com/stocks/NVDA")

# POST — 데이터 전송 (네이버 트렌드 API처럼 검색 조건을 보낼 때)
response = requests.post("https://api.example.com/search", json={"keyword": "AI"})
```

> **주의**: 대부분은 GET이지만, 네이버 데이터랩 같은 일부 API는 POST를 써야 한다.
> API 문서를 꼭 확인하자.

---

## 4. URL 구조 — 주소를 읽을 수 있어야 한다

### URL 분해하기

```
https://api.example.com:443/v1/stocks/NVDA?period=3m&format=json
  │          │             │  │    │    │       │           │
프로토콜   호스트(도메인)  포트 경로(path)      쿼리스트링(선택사항)
```

| 부분 | 예시 | 설명 |
|------|------|------|
| 프로토콜 | `https://` | 어떤 방식으로 통신할지 |
| 호스트 | `api.example.com` | 어느 서버에 보낼지 |
| 포트 | `:443` | 서버의 어느 문으로 들어갈지 (보통 생략) |
| 경로 | `/v1/stocks/NVDA` | 서버 안에서 어느 자원인지 |
| 쿼리스트링 | `?period=3m&format=json` | 추가 조건 (필터, 옵션 등) |

### 실제 API URL 예시

```
# 네이버 블로그 검색
https://openapi.naver.com/v1/search/blog?query=AI인프라&display=10&start=1

# 공공데이터 관광 통계
https://api.visitkorea.or.kr/openapi/service/rest/InrbndTrccStatService/getList?serviceKey=API키

# 카카오 주소 검색
https://dapi.kakao.com/v2/local/search/address.json?query=서울특별시 강남구
```

---

## 5. REST API — 가장 흔한 API 방식

### REST가 뭔가

**REST**(Representational State Transfer)는 API 설계 규칙이다.
규칙을 지킨 API를 "RESTful API" 또는 "REST API"라고 부른다.

### 핵심 규칙

**자원(Resource)은 URL로, 행동은 메서드로 표현한다.**

```
# 나쁜 예 (행동을 URL에 넣음)
GET  /getStockPrice?ticker=NVDA
POST /createNewUser
GET  /deleteStock?id=123

# 좋은 예 (REST 방식)
GET    /stocks/NVDA          → NVDA 주가 조회
POST   /stocks               → 새 주식 등록
PUT    /stocks/NVDA          → NVDA 정보 전체 수정
DELETE /stocks/NVDA          → NVDA 삭제
```

---

## 6. 오픈 API 데이터 수집 절차

### 전체 흐름

```
1. API 선택         어떤 데이터가 필요한가? → 어느 API를 쓸까?
        ↓
2. 가입 및 신청     개발자 사이트 회원가입 → 앱/프로젝트 등록
        ↓
3. API 키 발급      나를 식별하는 고유 코드 (비밀번호처럼 관리)
        ↓
4. 문서 읽기        어떤 URL로, 어떤 파라미터로 요청하나?
        ↓
5. 테스트 요청      소량으로 먼저 호출해서 응답 확인
        ↓
6. 코드 작성        Python으로 자동화
        ↓
7. 데이터 저장      CSV, JSON 등으로 저장
```

### API 키 관리 — 절대 잊으면 안 되는 것

```python
# 나쁜 예 — 코드에 직접 쓰면 GitHub에 올렸을 때 노출됨
API_KEY = "abc123xyz..."  # ❌ 절대 하지 말 것

# 좋은 예 — .env 파일에 저장하고 코드에서 불러오기
# .env 파일:
# NAVER_CLIENT_ID=abc123
# NAVER_CLIENT_SECRET=xyz789

from dotenv import load_dotenv
import os

load_dotenv()
client_id = os.getenv("NAVER_CLIENT_ID")      # ✅
client_secret = os.getenv("NAVER_CLIENT_SECRET")  # ✅
```

> `.env` 파일은 반드시 `.gitignore`에 추가한다.

---

## 7. Python으로 API 호출하기

### 기본 패턴

```python
import requests

# 요청
url = "https://api.example.com/data"
headers = {"Authorization": "Bearer API키"}
params = {"keyword": "AI", "period": "3m"}

response = requests.get(url, headers=headers, params=params)

# 상태 확인
print(response.status_code)  # 200이면 성공

# 데이터 파싱
data = response.json()  # JSON → Python 딕셔너리
print(data)
```

### 에러 처리 — 실전에서 꼭 필요한 코드

```python
import requests
import time

def call_api(url, headers, params, max_retries=3):
    """API 호출 + 에러 처리 기본 패턴"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 요청 횟수 초과 → 잠깐 기다렸다가 재시도
                print(f"요청 과다 (429). {2 ** attempt}초 후 재시도...")
                time.sleep(2 ** attempt)
            else:
                print(f"에러: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("타임아웃. 재시도...")
        except requests.exceptions.ConnectionError:
            print("연결 실패. 인터넷 확인 필요.")
            return None

    return None  # 최대 재시도 횟수 초과
```

---

## 8. 실습 예시 코드

### 네이버 블로그 검색 API

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def search_naver_blog(keyword, display=10):
    url = "https://openapi.naver.com/v1/search/blog"
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
        "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET"),
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": "sim",  # 정확도 순
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()["items"]
    else:
        print(f"에러: {response.status_code}")
        return []

# 사용
results = search_naver_blog("AI 인프라 투자")
for item in results:
    print(item["title"], item["link"])
```

### 네이버 데이터랩 트렌드 API (POST 방식 주의!)

```python
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_search_trend(keywords, start_date=None, end_date=None):
    """
    keywords: [{"groupName": "AI 반도체", "keywords": ["AI 반도체", "엔비디아"]}]
    """
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
        "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET"),
        "Content-Type": "application/json",
    }

    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

    # POST 방식 — body에 데이터를 담아서 보냄
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "week",        # day / week / month
        "keywordGroups": keywords,
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        return response.json()["results"]
    else:
        print(f"에러: {response.status_code} — {response.text}")
        return []

# 사용 예시
keywords = [
    {"groupName": "AI 반도체", "keywords": ["AI 반도체", "엔비디아", "NVDA"]},
    {"groupName": "전력 인프라", "keywords": ["전력 인프라", "변압기", "Eaton"]},
    {"groupName": "데이터센터", "keywords": ["데이터센터", "액체냉각"]},
]

results = get_search_trend(keywords)
for r in results:
    print(r["title"], r["data"][:3])  # 앞 3개만 출력
```

### 카카오 주소 → 좌표 변환 (지오코딩)

```python
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def geocode_address(address):
    """주소를 위도·경도로 변환"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {os.getenv('KAKAO_REST_API_KEY')}"}
    params = {"query": address}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        documents = response.json().get("documents", [])
        if documents:
            return {
                "lat": float(documents[0]["y"]),
                "lng": float(documents[0]["x"]),
            }
    return {"lat": None, "lng": None}

# CSV 파일의 주소들을 일괄 변환
df = pd.read_csv("hollys_stores.csv")
df[["lat", "lng"]] = df["address"].apply(
    lambda addr: pd.Series(geocode_address(addr))
)
df.to_csv("hollys_stores_with_coords.csv", index=False)
print(df.head())
```

---

## 9. 자주 나오는 데이터 형식

### JSON — API 응답의 99%

```json
{
    "ticker": "NVDA",
    "price": 875.4,
    "change": 2.3,
    "sectors": ["semiconductor", "AI"],
    "info": {
        "country": "US",
        "exchange": "NASDAQ"
    }
}
```

Python에서 다루는 법:

```python
data = response.json()

# 값 꺼내기
price = data["price"]              # 875.4
country = data["info"]["country"]  # "US"
first_sector = data["sectors"][0]  # "semiconductor"

# 리스트가 있을 때
for sector in data["sectors"]:
    print(sector)
```

---

## 10. 체크리스트 — API 쓸 때 매번 확인하기

```
□ API 키를 .env에 저장했나? (코드에 직접 쓰지 않았나?)
□ .env를 .gitignore에 추가했나?
□ 응답 status_code를 확인했나? (200인지 체크)
□ API 호출 한도(Rate Limit)를 확인했나? (너무 자주 호출하면 429)
□ timeout을 설정했나? (서버가 안 응답할 때 무한 대기 방지)
□ 데이터를 raw/ 폴더에 원본 그대로 저장했나?
□ API 문서에서 POST/GET 중 어느 방식인지 확인했나?
```

---

## 참고 사이트

| 서비스 | 개발자 사이트 |
|--------|-------------|
| 네이버 API | developers.naver.com |
| 카카오 API | developers.kakao.com |
| 공공데이터 포털 | data.go.kr |
| 구글 API (YouTube 등) | console.developers.google.com |
| SEC EDGAR API | data.sec.gov/api |

---

## 11. SEC EDGAR API — Phase 2 재무 데이터 수집

> Phase 2에서 수주잔고·book-to-bill·마진 등 실물 근거 데이터를 수집할 때 사용한다.
> 인증 키 없이 무료로 사용 가능. `requests` 패키지만 있으면 된다.

### 기본 구조

SEC EDGAR는 미국 상장 기업의 공식 재무 보고서(10-Q, 10-K)를 제공한다.

```
https://data.sec.gov/submissions/CIK{번호}.json    → 기업 기본 정보 + 보고서 목록
https://data.sec.gov/api/xbrl/companyfacts/CIK{번호}.json  → 전체 재무 데이터
```

### CIK 번호 찾기

CIK(Central Index Key)는 SEC가 기업에 부여하는 고유 번호다.

```python
import requests

def get_cik(company_name: str) -> str:
    """회사명으로 CIK 번호 검색"""
    url = "https://efts.sec.gov/LATEST/search-index?q={}&dateRange=custom&startdt=2020-01-01&forms=10-K"
    # 더 간단한 방법: EDGAR 전체 기업 목록 파일 사용
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers={"User-Agent": "yourname@email.com"})
    data = response.json()

    for item in data.values():
        if company_name.lower() in item["title"].lower():
            cik = str(item["cik_str"]).zfill(10)  # 10자리로 패딩
            print(f"{item['title']} → CIK: {cik}")
            return cik
    return None

# NVDA CIK 찾기
cik = get_cik("NVIDIA")  # → 0001045810
```

### 재무 데이터 수집 예시

```python
import requests
import pandas as pd

# SEC EDGAR는 User-Agent 헤더 필수 (없으면 차단됨)
HEADERS = {"User-Agent": "yourname@email.com"}

def fetch_edgar_facts(cik: str) -> dict:
    """기업의 전체 재무 데이터 수집"""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    return response.json()

def get_revenue(cik: str) -> pd.DataFrame:
    """분기별 매출 추출"""
    facts = fetch_edgar_facts(cik)
    # us-gaap 항목에서 매출 데이터 추출
    revenue_data = facts["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    df = pd.DataFrame(revenue_data)
    # 분기 보고서(10-Q)만 필터링
    df = df[df["form"] == "10-Q"].copy()
    df["end"] = pd.to_datetime(df["end"])
    return df[["end", "val", "form"]].sort_values("end")

# 사용 예시 — NVIDIA
nvda_revenue = get_revenue("0001045810")
print(nvda_revenue.tail(8))
```

### Phase 2에서 수집할 핵심 항목

| 항목 | XBRL 태그 | 설명 |
|------|-----------|------|
| 매출 | `Revenues` or `RevenueFromContractWithCustomerExcludingAssessedTax` | 분기 매출 |
| 영업이익 | `OperatingIncomeLoss` | 마진 추세 확인 |
| 수주잔고 | `RevenueRemainingPerformanceObligation` | backlog (있는 기업만) |
| R&D 비용 | `ResearchAndDevelopmentExpense` | 투자 강도 |

> **주의**: 수주잔고(backlog) XBRL 태그는 기업마다 다르거나 없을 수 있다.
> 없는 경우 어닝콜 PDF에서 수동으로 읽어야 한다 (Phase 2 계획대로).

### 호출 제한

- 초당 10회 이하 권장
- `User-Agent` 헤더 없으면 403 차단

---

> 업데이트 이력
>
> | 날짜 | 변경 내용 |
> |------|-----------|
> | 2026-03-24 | 초안 작성 (API 강의 내용 기반, 쉽게 재작성) |
> | 2026-03-25 | SEC EDGAR API 섹션 추가 (Phase 2 재무 데이터 수집용) |
