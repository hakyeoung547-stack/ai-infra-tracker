"""
bottleneck_score.py
섹터별 병목 점수를 계산한다.

현재 버전(v1): 가격 모멘텀 기반
  - 각 기업의 3M 수익률을 전체 평균과 비교한 상대 모멘텀으로 점수화
  - 향후 공급 제약 신호, 수요 압력 신호를 추가해 가중 합산

병목 점수 해석:
  +10% 초과 → 강한 병목 신호
  +5% ~ +10% → 중간 신호
  -5% ~ +5%  → 중립
  -5% 미만   → 병목 해소 or 수요 약화
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def load_latest_returns() -> pd.DataFrame:
    files = sorted((PROCESSED_DIR / "returns").glob("returns_*.csv"), reverse=True)
    if not files:
        raise FileNotFoundError("수익률 데이터 없음. returns.py를 먼저 실행하세요.")
    return pd.read_csv(files[0])


def calc_bottleneck_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    섹터별 병목 점수를 계산한다.

    현재 v1: 상대 모멘텀(3M) = 섹터 평균 3M 수익률 - 전체 평균 3M 수익률

    Returns:
        sector, avg_ret_3m, avg_ret_1m, bottleneck_score, signal 컬럼을 가진 DataFrame
    """
    overall_avg_3m = df["ret_3m"].mean()

    df_sector = (
        df.groupby("sector")
        .agg(
            avg_ret_1w=("ret_1w", "mean"),
            avg_ret_1m=("ret_1m", "mean"),
            avg_ret_3m=("ret_3m", "mean"),
            company_count=("ticker", "count"),
        )
        .round(2)
        .reset_index()
    )

    # 병목 점수 = 섹터 3M 수익률 - 전체 평균 3M 수익률
    df_sector["bottleneck_score"] = (df_sector["avg_ret_3m"] - overall_avg_3m).round(2)

    # 신호 레이블
    def label(score: float) -> str:
        if score > 10:
            return "강한 병목"
        elif score > 5:
            return "중간 병목"
        elif score > -5:
            return "중립"
        else:
            return "병목 약화"

    df_sector["signal"] = df_sector["bottleneck_score"].apply(label)
    df_sector = df_sector.sort_values("bottleneck_score", ascending=False)

    return df_sector


def calc_company_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """
    기업별 모멘텀 점수를 계산한다.
    섹터 평균 대비 해당 기업의 초과 성과를 본다.
    """
    sector_avg = df.groupby("sector")["ret_3m"].mean().rename("sector_avg_3m")
    df = df.merge(sector_avg, on="sector")
    df["momentum_vs_sector"] = (df["ret_3m"] - df["sector_avg_3m"]).round(2)
    return df


if __name__ == "__main__":
    df = load_latest_returns()

    print("\n[ 섹터별 병목 점수 ]")
    df_score = calc_bottleneck_score(df)
    print(df_score[["sector", "avg_ret_3m", "bottleneck_score", "signal"]].to_string(index=False))

    print("\n[ 기업별 섹터내 모멘텀 ]")
    df_momentum = calc_company_momentum(df)
    print(
        df_momentum[["ticker", "company", "sector", "ret_3m", "momentum_vs_sector"]]
        .sort_values("momentum_vs_sector", ascending=False)
        .to_string(index=False)
    )
