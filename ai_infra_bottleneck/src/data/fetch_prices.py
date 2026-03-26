"""
fetch_prices.py
주가 데이터를 yfinance로 수집해서 data/raw/prices/ 에 저장한다.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime
from src.data.db_manager import init_db, save_prices as db_save_prices

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "prices"
REF_DIR = Path(__file__).resolve().parents[2] / "data" / "reference"


def load_tickers() -> list[str]:
    """companies.csv에서 티커 목록을 읽어온다."""
    df = pd.read_csv(REF_DIR / "companies.csv")
    return df["ticker"].tolist()


def fetch_prices(tickers: list[str], period: str = "2y") -> dict[str, pd.DataFrame]:
    """
    yfinance로 주가 데이터를 수집한다.

    Args:
        tickers: 티커 리스트
        period: 수집 기간 ("1y", "2y", "5y" 등)

    Returns:
        {ticker: DataFrame} 딕셔너리
    """
    results = {}
    for ticker in tickers:
        try:
            df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
            if df.empty:
                print(f"[WARN] {ticker}: 데이터 없음")
                continue
            results[ticker] = df
            print(f"[OK] {ticker}: {len(df)}행 수집")
        except Exception as e:
            print(f"[ERR] {ticker}: {e}")
    return results


def save_prices(data: dict[str, pd.DataFrame]) -> None:
    """수집한 주가 데이터를 CSV + DB에 동시 저장한다."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.today().strftime("%Y%m%d")
    for ticker, df in data.items():
        path = RAW_DIR / f"{ticker}_{today}.csv"
        df.to_csv(path)
        print(f"[SAVE CSV] {path}")
        db_save_prices(ticker, df)


if __name__ == "__main__":
    init_db()
    tickers = load_tickers()
    data = fetch_prices(tickers)
    save_prices(data)
