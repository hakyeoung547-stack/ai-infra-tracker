"""
investment_signal.py
수익률 + 병목 점수 + 밸류에이션을 합쳐서 투자 신호를 계산한다.

[ 투자 신호 구성 ]

1. 모멘텀 점수 (40%)
   - 3M 수익률 기준 전체 기업 중 상위 몇 %인지를 0~10점으로 환산

2. 병목 점수 (30%)
   - 해당 기업이 속한 섹터의 병목 점수를 0~10점으로 환산

3. 밸류에이션 점수 (30%)
   - forwardPE 기준: 낮을수록 고점수 (단, None이면 중립 처리)
   - 성장주 특성상 PSR도 보조 지표로 함께 사용

[ 최종 신호 ]
  8점 이상  → BUY 관심
  5~8점    → WATCH 모니터링
  5점 미만  → NEUTRAL

주의: 이 신호는 투자 권유가 아님. 분석 보조 도구로만 사용할 것.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "fundamentals"
REF_DIR = Path(__file__).resolve().parents[2] / "data" / "reference"


def load_latest_returns() -> pd.DataFrame:
    files = sorted((PROCESSED_DIR / "returns").glob("returns_*.csv"), reverse=True)
    if not files:
        raise FileNotFoundError("수익률 데이터 없음. returns.py를 먼저 실행하세요.")
    return pd.read_csv(files[0])


def load_latest_fundamentals() -> pd.DataFrame | None:
    files = sorted(RAW_DIR.glob("fundamentals_*.csv"), reverse=True)
    if not files:
        return None
    return pd.read_csv(files[0])


def percentile_score(series: pd.Series) -> pd.Series:
    """시리즈를 백분위 기반 0~10점으로 환산한다. NaN은 5점(중립)."""
    ranks = series.rank(pct=True)
    return (ranks * 10).round(1).fillna(5.0)


def inverse_percentile_score(series: pd.Series) -> pd.Series:
    """낮을수록 좋은 지표(PER 등)를 역순으로 0~10점 환산. NaN은 5점."""
    ranks = series.rank(pct=True, ascending=False)
    return (ranks * 10).round(1).fillna(5.0)


def calc_sector_bottleneck_map(df_returns: pd.DataFrame) -> dict[str, float]:
    """섹터별 병목 점수를 딕셔너리로 반환한다."""
    overall_avg = df_returns["ret_3m"].mean()
    sector_avg = df_returns.groupby("sector")["ret_3m"].mean()
    raw_scores = sector_avg - overall_avg

    # 0~10점으로 정규화
    min_s, max_s = raw_scores.min(), raw_scores.max()
    if max_s == min_s:
        normalized = {s: 5.0 for s in raw_scores.index}
    else:
        normalized = {
            s: round((v - min_s) / (max_s - min_s) * 10, 1)
            for s, v in raw_scores.items()
        }
    return normalized


def build_investment_signal() -> pd.DataFrame:
    """
    투자 신호 테이블을 생성한다.

    Returns:
        ticker, company, sector, momentum_score, bottleneck_score,
        valuation_score, total_score, signal 컬럼을 포함하는 DataFrame
    """
    df_returns = load_latest_returns()
    df_fundamentals = load_latest_fundamentals()

    # --- 1. 모멘텀 점수 ---
    df = df_returns.copy()
    df["momentum_score"] = percentile_score(df["ret_3m"])

    # --- 2. 병목 점수 ---
    sector_bottleneck = calc_sector_bottleneck_map(df_returns)
    df["bottleneck_score"] = df["sector"].map(sector_bottleneck).fillna(5.0)

    # --- 3. 밸류에이션 점수 ---
    if df_fundamentals is not None:
        df = df.merge(df_fundamentals[["ticker", "forwardPE", "priceToSales"]], on="ticker", how="left")
        # forwardPE: 낮을수록 좋음 (성장성 없는 고PER은 페널티)
        # 단, AI 성장주는 PER이 높을 수 있으므로 PSR도 함께 반영
        df["pe_score"] = inverse_percentile_score(df["forwardPE"])
        df["psr_score"] = inverse_percentile_score(df["priceToSales"])
        df["valuation_score"] = (df["pe_score"] * 0.6 + df["psr_score"] * 0.4).round(1)
    else:
        # 펀더멘털 데이터 없으면 중립 처리
        df["valuation_score"] = 5.0

    # --- 4. 총점 ---
    df["total_score"] = (
        df["momentum_score"] * 0.40
        + df["bottleneck_score"] * 0.30
        + df["valuation_score"] * 0.30
    ).round(1)

    # --- 5. 신호 레이블 ---
    def signal_label(score: float) -> str:
        if score >= 8:
            return "BUY 관심"
        elif score >= 5:
            return "WATCH"
        else:
            return "NEUTRAL"

    df["signal"] = df["total_score"].apply(signal_label)

    cols = [
        "ticker", "company", "sector",
        "ret_1m", "ret_3m",
        "momentum_score", "bottleneck_score", "valuation_score",
        "total_score", "signal",
    ]
    return df[cols].sort_values("total_score", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    df_signal = build_investment_signal()
    print("\n[ 투자 신호 테이블 ]\n")
    print(df_signal.to_string(index=False))

    print("\n[ BUY 관심 기업 ]")
    buy = df_signal[df_signal["signal"] == "BUY 관심"]
    if buy.empty:
        print("  현재 없음")
    else:
        print(buy[["ticker", "company", "sector", "total_score"]].to_string(index=False))
