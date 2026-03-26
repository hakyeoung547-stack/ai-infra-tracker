"""
returns.py
수집된 주가 데이터로 다기간 수익률을 계산한다.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "prices"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "returns"
REF_DIR = Path(__file__).resolve().parents[2] / "data" / "reference"

PERIODS = {
    "ret_1w": 5,
    "ret_1m": 21,
    "ret_3m": 63,
    "ret_6m": 126,
    "ret_1y": 252,
}


def load_latest_prices(ticker: str) -> pd.Series | None:
    """티커의 가장 최근 CSV 파일을 불러온다."""
    files = sorted(RAW_DIR.glob(f"{ticker}_*.csv"), reverse=True)
    if not files:
        return None
    df = pd.read_csv(files[0], index_col=0, parse_dates=True)
    return df["Close"]


def calc_returns(prices: pd.Series) -> dict:
    """다기간 수익률을 계산한다."""
    result = {}
    for name, days in PERIODS.items():
        if len(prices) >= days + 1:
            ret = (prices.iloc[-1] / prices.iloc[-days - 1]) - 1
            result[name] = round(ret * 100, 2)
        else:
            result[name] = None

    # YTD 수익률
    year_start = prices[prices.index.year == prices.index[-1].year].iloc[0]
    result["ret_ytd"] = round(((prices.iloc[-1] / year_start) - 1) * 100, 2)

    return result


def build_returns_table() -> pd.DataFrame:
    """전체 기업의 수익률 테이블을 만든다."""
    df_companies = pd.read_csv(REF_DIR / "companies.csv")
    rows = []

    for _, row in df_companies.iterrows():
        ticker = row["ticker"]
        prices = load_latest_prices(ticker)
        if prices is None:
            print(f"[SKIP] {ticker}: 데이터 없음")
            continue

        ret = calc_returns(prices)
        ret["ticker"] = ticker
        ret["company"] = row["company"]
        ret["sector"] = row["sector"]
        ret["bottleneck_relevance"] = row["bottleneck_relevance"]
        rows.append(ret)

    df = pd.DataFrame(rows)
    cols = ["ticker", "company", "sector", "bottleneck_relevance",
            "ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_1y", "ret_ytd"]
    return df[cols]


if __name__ == "__main__":
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_returns = build_returns_table()
    today = datetime.today().strftime("%Y%m%d")
    out = PROCESSED_DIR / f"returns_{today}.csv"
    df_returns.to_csv(out, index=False)
    print(f"\n[SAVE] {out}")
    print(df_returns.to_string(index=False))
