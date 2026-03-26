"""
sector_compare.py
섹터별 성과를 집계하고 비교 테이블을 만든다.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def load_latest_returns() -> pd.DataFrame:
    """가장 최근 수익률 데이터를 불러온다."""
    files = sorted((PROCESSED_DIR / "returns").glob("returns_*.csv"), reverse=True)
    if not files:
        raise FileNotFoundError("수익률 데이터가 없습니다. returns.py를 먼저 실행하세요.")
    return pd.read_csv(files[0])


def sector_summary(df: pd.DataFrame) -> pd.DataFrame:
    """섹터별 평균 수익률 요약 테이블을 만든다."""
    ret_cols = ["ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_1y", "ret_ytd"]
    df_sector = (
        df.groupby("sector")[ret_cols]
        .mean()
        .round(2)
        .reset_index()
        .sort_values("ret_3m", ascending=False)
    )
    return df_sector


def top_performers(df: pd.DataFrame, n: int = 5, period: str = "ret_1m") -> pd.DataFrame:
    """지정 기간 기준 상위 기업을 반환한다."""
    return df.nlargest(n, period)[["ticker", "company", "sector", period]]


def bottom_performers(df: pd.DataFrame, n: int = 5, period: str = "ret_1m") -> pd.DataFrame:
    """지정 기간 기준 하위 기업을 반환한다."""
    return df.nsmallest(n, period)[["ticker", "company", "sector", period]]


if __name__ == "__main__":
    df = load_latest_returns()

    print("\n[ 섹터별 평균 수익률 ]")
    print(sector_summary(df).to_string(index=False))

    print("\n[ 1개월 상위 5개 기업 ]")
    print(top_performers(df).to_string(index=False))

    print("\n[ 1개월 하위 5개 기업 ]")
    print(bottom_performers(df).to_string(index=False))
