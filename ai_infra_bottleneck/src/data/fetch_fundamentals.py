"""
fetch_fundamentals.py
yfinance로 밸류에이션 지표를 수집해서 data/raw/fundamentals/ 에 저장한다.

수집 항목:
- trailingPE     : 후행 PER
- forwardPE      : 선행 PER
- priceToSales   : PSR
- priceToBook    : PBR
- marketCap      : 시가총액
- revenueGrowth  : 매출 성장률 (YoY)
- grossMargins   : 매출총이익률
- returnOnEquity : ROE
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "fundamentals"
REF_DIR = Path(__file__).resolve().parents[2] / "data" / "reference"

FIELDS = [
    "trailingPE",
    "forwardPE",
    "priceToSales",
    "priceToBook",
    "marketCap",
    "revenueGrowth",
    "grossMargins",
    "returnOnEquity",
]


def load_tickers() -> list[str]:
    df = pd.read_csv(REF_DIR / "companies.csv")
    return df["ticker"].tolist()


def fetch_fundamentals(tickers: list[str]) -> pd.DataFrame:
    rows = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            row = {"ticker": ticker}
            for field in FIELDS:
                row[field] = info.get(field, None)
            rows.append(row)
            print(f"[OK] {ticker}")
        except Exception as e:
            print(f"[ERR] {ticker}: {e}")
    return pd.DataFrame(rows)


def save_fundamentals(df: pd.DataFrame) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.today().strftime("%Y%m%d")
    path = RAW_DIR / f"fundamentals_{today}.csv"
    df.to_csv(path, index=False)
    print(f"[SAVE] {path}")


if __name__ == "__main__":
    tickers = load_tickers()
    df = fetch_fundamentals(tickers)
    save_fundamentals(df)
