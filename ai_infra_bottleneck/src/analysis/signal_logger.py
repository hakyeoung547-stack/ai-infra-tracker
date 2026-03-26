"""
signal_logger.py

병목 신호를 생성, 기록, 검증하는 모듈.

사용법:
    from src.analysis.signal_logger import determine_signal, log_signal, log_validation, review_accuracy
"""

from pathlib import Path
import pandas as pd
from datetime import date, datetime

# 경로 설정
ROOT = Path(__file__).resolve().parents[2]
SIGNAL_LOG_PATH = ROOT / "data" / "signals" / "signal_log.csv"
VALIDATION_PATH = ROOT / "data" / "signals" / "signal_validation.csv"

# CSV 헤더 정의
SIGNAL_LOG_COLS = [
    "week_date", "sector", "score_v1", "score_trend_4w",
    "q1_trend", "q2_fresh", "q3_macro_sep", "q4_physical",
    "final_signal", "spy_3m_return", "sector_3m_return", "avg_3m_return"
]

VALIDATION_COLS = [
    "signal_date", "sector", "original_signal",
    "return_4w", "return_8w", "outcome", "error_type",
    "q_missed", "threshold_verdict", "lesson_tag", "notes"
]


# ─────────────────────────────────────────────
# 신호 판단 로직
# ─────────────────────────────────────────────

def _check_q1(score_trend_4w: float) -> str:
    """Q1: 추세 방향 — 4주 추세가 상승 중인가"""
    return "PASS" if score_trend_4w > 0 else "FAIL"


def _check_q2(weeks_since_breakout) -> str:
    """Q2: 돌파 신선도 — 임계값 초과 후 8주 이내인가

    Args:
        weeks_since_breakout: 임계값 첫 초과 후 경과 주수. None이면 아직 초과 안 됨.
    """
    if weeks_since_breakout is None:
        return "FAIL"
    return "PASS" if weeks_since_breakout <= 8 else "FAIL"


def _check_q3(sector_3m: float, spy_3m: float, threshold: float = 5.0) -> str:
    """Q3: 매크로 분리 — 섹터가 SPY 대비 5%p 이상 초과 수익인가"""
    return "PASS" if (sector_3m - spy_3m) > threshold else "FAIL"


def determine_signal(
    score_v1: float,
    score_trend_4w: float,
    weeks_since_breakout,
    sector_3m: float,
    spy_3m: float,
    q4_physical: str = "NA",
) -> dict:
    """
    Q1~Q4 체크를 수행하고 최종 신호 코드를 반환한다.

    Args:
        score_v1: 섹터 3M 수익률 - AI 인프라 평균 3M 수익률 (%)
        score_trend_4w: score_v1 현재값 - 4주 전 값
        weeks_since_breakout: 임계값(5%) 최초 초과 후 경과 주수. 미초과 시 None.
        sector_3m: 해당 섹터 3개월 수익률 (%)
        spy_3m: SPY 3개월 수익률 (%)
        q4_physical: 수동 입력값 — "PASS" / "FAIL" / "NA"

    Returns:
        dict with keys: q1, q2, q3, q4, final_signal
    """
    q1 = _check_q1(score_trend_4w)
    q2 = _check_q2(weeks_since_breakout)
    q3 = _check_q3(sector_3m, spy_3m)
    q4 = q4_physical.upper()

    na_q4 = q4 == "NA"

    # 신호 판단 규칙
    if q1 == "PASS" and q2 == "PASS" and q3 == "PASS" and q4 == "PASS" and score_v1 >= 10:
        final_signal = "STRONG_BUY"
    elif q1 == "PASS" and q2 == "PASS" and q3 == "PASS" and na_q4 and 5 <= score_v1 < 10:
        final_signal = "EARLY_ENTRY"
    elif q1 == "PASS" and q2 == "PASS" and q3 == "FAIL":
        final_signal = "MACRO_CAUTION"
    elif q1 == "FAIL" and score_v1 >= 15:
        final_signal = "PEAK_WARNING"
    elif q1 == "PASS" and sum(x == "PASS" for x in [q1, q2, q3]) < 3:
        final_signal = "MONITOR"
    elif score_v1 < 0 and q4 == "PASS":
        final_signal = "CONTRARIAN"
    else:
        final_signal = "NEUTRAL"

    return {
        "q1_trend": q1,
        "q2_fresh": q2,
        "q3_macro_sep": q3,
        "q4_physical": q4,
        "final_signal": final_signal,
    }


# ─────────────────────────────────────────────
# 신호 기록
# ─────────────────────────────────────────────

def log_signal(
    week_date: str,
    sector: str,
    score_v1: float,
    score_trend_4w: float,
    weeks_since_breakout,
    spy_3m_return: float,
    sector_3m_return: float,
    avg_3m_return: float,
    q4_physical: str = "NA",
) -> dict:
    """
    신호를 계산하고 signal_log.csv에 한 행을 추가한다.

    Returns:
        추가된 행 데이터 (dict)
    """
    result = determine_signal(
        score_v1=score_v1,
        score_trend_4w=score_trend_4w,
        weeks_since_breakout=weeks_since_breakout,
        sector_3m=sector_3m_return,
        spy_3m=spy_3m_return,
        q4_physical=q4_physical,
    )

    row = {
        "week_date": week_date,
        "sector": sector,
        "score_v1": round(score_v1, 2),
        "score_trend_4w": round(score_trend_4w, 2),
        "q1_trend": result["q1_trend"],
        "q2_fresh": result["q2_fresh"],
        "q3_macro_sep": result["q3_macro_sep"],
        "q4_physical": result["q4_physical"],
        "final_signal": result["final_signal"],
        "spy_3m_return": round(spy_3m_return, 2),
        "sector_3m_return": round(sector_3m_return, 2),
        "avg_3m_return": round(avg_3m_return, 2),
    }

    _append_row(SIGNAL_LOG_PATH, row, SIGNAL_LOG_COLS)
    return row


def log_validation(
    signal_date: str,
    sector: str,
    original_signal: str,
    return_4w: float,
    return_8w: float,
    outcome: str,
    error_type: str = "—",
    q_missed: str = "NONE",
    threshold_verdict: str = "OK",
    lesson_tag: str = "GOOD_SIGNAL",
    notes: str = "",
) -> dict:
    """
    신호 검증 결과를 signal_validation.csv에 한 행을 추가한다.

    outcome 허용값: CORRECT, EARLY, LATE, WRONG_DIR, PARTIAL, NOISE
    error_type 허용값: ALREADY_PRICED, MACRO_SURPRISE, FALSE_BREAKOUT,
                       PHYSICAL_LAG, THRESHOLD_ISSUE, BUBBLE, SPY_MISSED, —
    """
    row = {
        "signal_date": signal_date,
        "sector": sector,
        "original_signal": original_signal,
        "return_4w": round(return_4w, 2),
        "return_8w": round(return_8w, 2),
        "outcome": outcome,
        "error_type": error_type,
        "q_missed": q_missed,
        "threshold_verdict": threshold_verdict,
        "lesson_tag": lesson_tag,
        "notes": notes,
    }

    _append_row(VALIDATION_PATH, row, VALIDATION_COLS)
    return row


# ─────────────────────────────────────────────
# 정확도 리뷰
# ─────────────────────────────────────────────

def review_accuracy(last_n_weeks=None) -> dict:
    """
    signal_validation.csv를 읽어 시스템 성능 요약을 반환한다.

    Args:
        last_n_weeks: 최근 N주만 분석. None이면 전체.

    Returns:
        dict with keys: overall_accuracy, by_signal, by_sector, top_errors, q_missed_counts
    """
    if not VALIDATION_PATH.exists():
        return {"error": "signal_validation.csv 파일이 없습니다."}

    df = pd.read_csv(VALIDATION_PATH)

    if df.empty:
        return {"error": "검증 데이터가 없습니다."}

    if last_n_weeks is not None:
        df["signal_date"] = pd.to_datetime(df["signal_date"])
        cutoff = pd.Timestamp.today() - pd.Timedelta(weeks=last_n_weeks)
        df = df[df["signal_date"] >= cutoff]

    total = len(df)
    correct = (df["outcome"] == "CORRECT").sum()

    result = {
        "total_signals": total,
        "overall_accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        "by_signal": (
            df.groupby("original_signal")["outcome"]
            .value_counts(normalize=True)
            .round(3)
            .to_dict()
        ),
        "by_sector": (
            df.groupby("sector")["outcome"]
            .apply(lambda x: round((x == "CORRECT").sum() / len(x) * 100, 1))
            .sort_values(ascending=False)
            .to_dict()
        ),
        "top_errors": (
            df[df["error_type"] != "—"]["error_type"]
            .value_counts()
            .head(5)
            .to_dict()
        ),
        "q_missed_counts": (
            df[df["q_missed"] != "NONE"]["q_missed"]
            .value_counts()
            .to_dict()
        ),
    }

    return result


def print_review(last_n_weeks=None) -> None:
    """review_accuracy 결과를 읽기 쉽게 출력한다."""
    r = review_accuracy(last_n_weeks)

    if "error" in r:
        print(r["error"])
        return

    period = f"최근 {last_n_weeks}주" if last_n_weeks else "전체 기간"
    print(f"\n{'='*50}")
    print(f"신호 정확도 리뷰 — {period}")
    print(f"{'='*50}")
    print(f"총 신호 수  : {r['total_signals']}개")
    print(f"전체 정확도 : {r['overall_accuracy']}%")

    print("\n[섹터별 정확도]")
    for sector, acc in r["by_sector"].items():
        print(f"  {sector:25s}: {acc}%")

    print("\n[주요 오류 유형]")
    for err, cnt in r["top_errors"].items():
        print(f"  {err:20s}: {cnt}회")

    print("\n[누락된 체크]")
    for q, cnt in r["q_missed_counts"].items():
        print(f"  {q}: {cnt}회")


# ─────────────────────────────────────────────
# 내부 유틸리티
# ─────────────────────────────────────────────

def _append_row(path: Path, row: dict, columns: list) -> None:
    """CSV 파일에 한 행을 추가한다. 파일이 없으면 헤더와 함께 생성한다."""
    path.parent.mkdir(parents=True, exist_ok=True)

    df_new = pd.DataFrame([row], columns=columns)

    if path.exists():
        df_existing = pd.read_csv(path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_csv(path, index=False)
