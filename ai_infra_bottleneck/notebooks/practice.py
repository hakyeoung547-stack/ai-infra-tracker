# ── 이전 코드 (문제 있음) ──────────────────────────────────────
# from Fastapi import FastAPI   # ❌ 대소문자 오류
# import yfinance as yf
# import asyncio
# app=FastAPI()
#
# @app.get("/stock/{ticker}")
# async def get_stock_info(ticker: str):
#     stock=yf.Ticker(ticker)
#     return stock.info
#
# AAPL_info=asyncio.run(get_stock_info("AAPL"))  # ❌ 라우터 함수를 직접 호출하면 안 됨
# print(AAPL_info)
# ─────────────────────────────────────────────────────────────────

# ── 수정 전 코드 (문제 있음) ───────────────────────────────────────
# from fastapi import FastAPI
# import yfinance as yf
#
# app = FastAPI()
#
# @app.get("/stock/{ticker}")
# async def get_stock_info(ticker: str):
#     stock = yf.Ticker(ticker)
#     return stock.info
#
# from fastapi import FastAPI, Form   # ❌ FastAPI 중복 import
#
# @app.post("/stock")
# async def slack_command(
#     text: str= Form(...),
#     user: str= Form(...),      # ❌ 슬랙이 보내는 필드는 user_id (user 아님)
#     command: str= Form()       # ❌ Form(...) 으로 필수 표시 해야 함
# ):
#     if command == "/stock":
#         return {"text": f"주식 정보 요청: {text}", "stock_info": stock.info}
#         # ❌ stock이 이 함수 안에서 정의된 적 없음 (stock = yf.Ticker(text) 빠짐)
#         # ❌ 응답 형식이 Slack 포맷이 아님 (response_type 필드 없음)
# ─────────────────────────────────────────────────────────────────

# ── 수정 코드 ─────────────────────────────────────────────────────
from fastapi import FastAPI, Form
import yfinance as yf

app = FastAPI()


@app.get("/stock/{ticker}")
async def get_stock_info(ticker: str):
    stock = yf.Ticker(ticker)
    return stock.info


@app.post("/slack")
async def slack_stock_command(
    command: str = Form(...),   # "/stock"
    text: str = Form(...),      # "AAPL" — 슬랙에서 /stock 뒤에 입력한 텍스트
    user_id: str = Form(...),   # 슬랙 유저 ID
):
    if command != "/stock":
        return {"response_type": "ephemeral", "text": f"알 수 없는 명령어: {command}"}

    ticker = text.strip().upper()
    stock = yf.Ticker(ticker)
    info = stock.info

    name = info.get("longName", ticker)
    price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
    change_pct = info.get("regularMarketChangePercent", 0)
    market_cap = info.get("marketCap", "N/A")

    message = (
        f"*{name} ({ticker})*  |  요청자: <@{user_id}>\n"
        f"현재가: ${price}\n"
        f"등락률: {change_pct:.2f}%\n"
        f"시가총액: ${market_cap:,}"
    )

    # Slack slash command 응답 형식
    return {
        "response_type": "in_channel",  # 채널 전체 공개. 본인만 보려면 "ephemeral"
        "text": message,
    }


# ── 실행 방법 ───────────────────────────────────────────────────────
# 1. 서버 실행
#    uvicorn practice:app --reload
#
# 2. 외부 노출 (로컬 개발 시 ngrok 사용)
#    ngrok http 8000
#    → https://xxxx.ngrok.io 같은 URL 생성됨
#
# 3. Slack App 설정
#    https://api.slack.com/apps → 내 앱 선택
#    Slash Commands → /stock 추가
#    Request URL: https://xxxx.ngrok.io/slack/stock
#
# 4. 슬랙에서 테스트
#    /stock AAPL
# ──────────────────────────────────────────────────────────────────