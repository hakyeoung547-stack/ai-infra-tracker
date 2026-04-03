# FastAPI와 MCP가 비슷하다?

> 작성일: 2026-04-01
> 태그: Python, FastAPI, MCP, HTTP, API, 서버, 초보자

---

## 구조를 나란히 놓으면

```python
# FastAPI 핵심 구조
from fastapi import FastAPI

app = FastAPI()

@app.get("/stock/{ticker}")
async def get_stock_info(ticker: str):
    stock = ...   # 데이터 조회
    return ...    # 결과 반환
```

```python
# MCP 핵심 구조
from fastmcp import FastMCP

mcp = FastMCP("stock_server")

@mcp.tool()
def get_stock_info(ticker: str):
    stock = ...   # 데이터 조회
    return ...    # 결과 반환

mcp.run()
```

나란히 보면 거의 똑같다.
둘 다 **"요청 → 함수 실행 → 결과 반환"** 흐름이다.

---

## 그런데 완전히 같지는 않다

구조는 비슷하지만, **요청 방식과 통신 인터페이스**가 다르다.

| 구분 | FastAPI | FastMCP |
|------|---------|---------|
| 앱 초기화 | `app = FastAPI()` | `mcp = FastMCP("...")` |
| 엔드포인트 등록 | `@app.post("/slack")` | `@mcp.tool()` |
| 함수 본체 | yfinance 로직 | yfinance 로직 (동일) |
| 실행 | uvicorn | `mcp.run()` |
| 통신 방식 | HTTP 기반 (GET, POST, URL) | MCP 프로토콜 기반 (AI가 tool 호출) |

---

## 사용자가 다르다

| 구분 | FastAPI (웹 인터페이스) | MCP (AI 인터페이스) |
|------|----------------------|------------------|
| 핵심 식별자 | URL 경로 (`/stock/{ticker}`) | 도구 이름 + 설명 (`get_stock_price`) |
| 사용자 | 브라우저에 주소를 치는 사람 | 질문을 듣고 도구를 고르는 AI |
| 필수 요소 | GET, POST 같은 메서드 | **함수의 기능 설명 (Docstring)** |

FastAPI는 👉 **URL이라는 "주소"로** 기능을 구분한다.

MCP는 👉 **함수 이름 + 설명으로 "도구"를** 구분한다.

FastAPI는 사람이 직접 호출하지만, MCP는 AI가 상황을 이해하고 적절한 함수를 선택해서 호출한다.

> **핵심 결론**
> MCP 인터페이스는 "AI가 내 코드를 함수처럼 선택해서 호출할 수 있게 만든 실행 인터페이스"다.

---

## HTTP 메서드 사용법

GET/POST는 내가 마음대로 정하는 것이 아니라, **누가 요청을 보내느냐**에 따라 결정된다.

> GET → 데이터 조회 (읽기)
> POST → 데이터 전송/생성 (쓰기)

---

### 나쁜 예 vs 좋은 예

나쁜 예 — 주소에 행동을 구구절절 써놓은 것

```
GET /getStockInfoByName/samsung
POST /createAndSendSlackMessage
```

좋은 예 — 대상(데이터)만 주소에 적고, 행동은 HTTP 메서드로 결정

```
GET  /stock/samsung
POST /slack
```

HTTP 메서드(`GET`, `POST`)가 이미 행동을 말해주고 있으니, 주소에는 **대상만** 쓰면 된다.
`GET /stock/samsung`만 봐도 "NVDA 정보를 가져오는 거구나"라고 누구나 예측할 수 있다.

---

## GET — 내가 설계하는 API

내가 만든 API는 내가 주인이다.

### 1. 주소 이름을 내 마음대로 (Naming)

```
GET /stock/samsung       # 종목명으로 조회
GET /code/005939         # 종목코드로 조회
GET /price/now/samsung   # 현재가만 조회
```

### 2. 가공된 결과물 (Output Design)

똑같은 데이터를 어떻게 보여줄지도 내 자유다.

```
# 그냥 숫자만
75000

# 깔끔한 문장
"현재 삼성전자의 주가는 75,000원입니다."

# 데이터 묶음 (JSON)
{"name": "삼성전자", "price": 75000, "status": "상승"}
```

### 3. 필터링 옵션 (Query Parameters)

불러올 때 조건을 다는 것도 내 마음이다.

```
GET /stock/samsung?days=7        # 최근 7일치 데이터만
GET /stock/samsung?currency=usd  # 달러로 환산해서
```

---

## POST — 외부 서비스가 규칙을 정한다

`/slack` 엔드포인트는 상황이 다르다.

내가 요청을 보내는 것이 아니라, **Slack이라는 외부 서비스가 내 서버로 요청을 보내는 구조**다.
Slack은 이미 요청 방식을 POST로 정해두었기 때문에, 나는 그 규칙에 맞춰서 `@app.post("/slack")`으로 만들어야 한다.

> Slack(POST) → 슬랙이 주는 데이터를 **정해진 규격대로 받아내는 것**에 집중
> 내 API(GET) → 어떤 주소로, 어떤 데이터를, 어떤 모양으로 보여줄까를 **내가 직접 기획하고 설계**

---

## 한 줄 정리

> HTTP 엔드포인트는 요청이 들어오는 주소이고, 그 요청 방식(GET/POST)은 **요청을 보내는 주체**에 따라 결정된다.
