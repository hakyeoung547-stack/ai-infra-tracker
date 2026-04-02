"""
weekly_report.py
주간 Markdown 리포트를 자동 생성한다.

데이터 흐름:
  returns.csv + fundamentals.csv
      ↓
  investment_signal.build_investment_signal()
  bottleneck_score.calc_bottleneck_score()
  sector_compare.sector_summary()
      ↓
  weekly_template.md → reports/weekly/YYYY-WW_weekly.md
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis.sector_compare import load_latest_returns, sector_summary, top_performers, bottom_performers
from src.analysis.bottleneck_score import calc_bottleneck_score
from src.analysis.investment_signal import build_investment_signal

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports" / "weekly"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def df_to_md_table(df: pd.DataFrame) -> str:
    """DataFrame을 Markdown 테이블 문자열로 변환한다."""
    if df.empty:
        return "_없음_"
    header = "| " + " | ".join(df.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.values]
    return "\n".join([header, separator] + rows)


def generate_report() -> Path:
    today = datetime.today()

    # --- 데이터 로드 ---
    df_returns = load_latest_returns()
    df_sector = sector_summary(df_returns).sort_values("ret_1m", ascending=False)
    df_bottleneck = calc_bottleneck_score(df_returns)
    df_signal = build_investment_signal()

    # --- 요약 수치 ---
    best_row = df_sector.iloc[0]
    worst_row = df_sector.iloc[-1]
    top_bn = df_bottleneck.iloc[0]

    # --- 투자 신호 분리 ---
    df_buy = df_signal[df_signal["signal"] == "BUY 관심"][
        ["ticker", "company", "sector", "ret_1m", "ret_3m", "total_score"]
    ]
    df_watch = df_signal[df_signal["signal"] == "WATCH"][
        ["ticker", "company", "sector", "ret_1m", "ret_3m", "total_score"]
    ]

    # --- 병목 테이블 ---
    df_bn_table = df_bottleneck[["sector", "avg_ret_3m", "bottleneck_score", "signal"]]
    df_bn_table.columns = ["섹터", "3M 평균 수익률(%)", "병목 점수", "신호"]

    # --- 섹터 성과 테이블 ---
    df_sector_display = df_sector[["sector", "ret_1w", "ret_1m", "ret_3m"]]
    df_sector_display.columns = ["섹터", "1W(%)", "1M(%)", "3M(%)"]

    # --- 템플릿 렌더링 ---
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    tmpl = env.get_template("weekly_template.md")
    content = tmpl.render(
        report_date=today.strftime("%Y년 %m월 %d일"),
        base_date=today.strftime("%Y-%m-%d"),
        company_count=len(df_returns),
        total_ret_1w=round(df_returns["ret_1w"].mean(), 2),
        best_sector=best_row["sector"],
        best_sector_ret=best_row["ret_1m"],
        worst_sector=worst_row["sector"],
        worst_sector_ret=worst_row["ret_1m"],
        top_bottleneck_sector=top_bn["sector"],
        top_bottleneck_score=top_bn["bottleneck_score"],
        buy_table=df_to_md_table(df_buy),
        watch_table=df_to_md_table(df_watch),
        bottleneck_table=df_to_md_table(df_bn_table),
        sector_table=df_to_md_table(df_sector_display),
        top_performers_table=df_to_md_table(
            top_performers(df_returns)[["ticker", "company", "sector", "ret_1m"]]
        ),
        bottom_performers_table=df_to_md_table(
            bottom_performers(df_returns)[["ticker", "company", "sector", "ret_1m"]]
        ),
    )

    # --- 저장 ---
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    week_num = today.strftime("%Y-W%W")
    out = REPORTS_DIR / f"{week_num}_weekly.md"
    out.write_text(content, encoding="utf-8")
    print(f"[SAVE] {out}")
    return out


if __name__ == "__main__":
    import sys

    # src/analysis 경로를 import 경로에 추가
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
    generate_report()
