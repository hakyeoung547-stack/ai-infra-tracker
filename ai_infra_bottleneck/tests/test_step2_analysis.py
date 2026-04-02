"""
=============================================================================
STEP 2 — 분석 레이어 (src/analysis/)
=============================================================================

실행 순서 (weekly):
  ① returns.py          → CSV 주가 → 다기간 수익률 테이블 생성
  ② sector_compare.py   → 수익률 테이블 → 섹터별 요약 / 상하위 기업
  ③ bottleneck_score.py → 수익률 테이블 → 섹터 병목 점수
  ④ investment_signal.py→ 수익률 + 밸류에이션 → 투자 신호 (BUY/WATCH/NEUTRAL)
  ⑤ signal_logger.py    → 신호 계산 + CSV 기록 + 정확도 리뷰

이 파일의 모든 테스트는 현재 RED(실패) 상태입니다.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "analysis"))


# =============================================================================
# ① returns.py
#
# 역할: CSV 주가 파일로부터 다기간 수익률 계산
#   · load_latest_prices(ticker) → 가장 최근 CSV 읽어서 Close 시리즈 반환
#   · calc_returns(prices)       → 1W/1M/3M/6M/1Y/YTD 수익률 dict 반환
#   · build_returns_table()      → 전체 기업 수익률 DataFrame 생성
#
# PERIODS 상수:
#   ret_1w=5일, ret_1m=21일, ret_3m=63일, ret_6m=126일, ret_1y=252일
# =============================================================================

class TestReturns:

    def _make_price_series(self, n_days=300, start_price=100.0, growth=0.001):
        """테스트용 가짜 주가 시리즈 생성"""
        idx = pd.bdate_range("2025-01-01", periods=n_days)
        prices = [start_price * (1 + growth) ** i for i in range(n_days)]
        return pd.Series(prices, index=idx, name="Close")

    def test_calc_returns_keys(self):
        """
        [calc_returns]
        반환 dict에 ret_1w, ret_1m, ret_3m, ret_6m, ret_1y, ret_ytd 키가 있어야 한다.
        """
        from src.analysis.returns import calc_returns
        prices = self._make_price_series(300)
        result = calc_returns(prices)

        expected_keys = {"ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_1y", "ret_ytd"}
        assert expected_keys == set(result.keys()), \
            f"반환 dict 키가 달라야 한다. 현재: {set(result.keys())}"

    def test_calc_returns_positive_for_rising_stock(self):
        """
        [calc_returns]
        계속 상승하는 주가 → 모든 수익률이 양수여야 한다.
        """
        from src.analysis.returns import calc_returns
        prices = self._make_price_series(300, growth=0.002)  # 매일 0.2% 상승
        result = calc_returns(prices)

        for key, val in result.items():
            if val is not None:
                assert val > 0, f"{key}가 양수여야 한다. 현재: {val}"

    def test_calc_returns_none_when_insufficient_data(self):
        """
        [calc_returns]
        데이터가 충분하지 않은 기간(예: 5일치 데이터로 1Y 수익률)은 None이어야 한다.
        """
        from src.analysis.returns import calc_returns
        prices = self._make_price_series(10)  # 10일치만
        result = calc_returns(prices)

        # 252일이 필요한 1Y는 None이어야 함
        assert result["ret_1y"] is None, "데이터 부족 시 ret_1y는 None이어야 한다"

    def test_build_returns_table_columns(self, tmp_path, monkeypatch):
        """
        [build_returns_table]
        반환 DataFrame에 최소한 ticker, sector, ret_1m, ret_3m 컬럼이 있어야 한다.
        """
        from src.analysis import returns as ret_module

        # companies.csv 가짜로 교체
        fake_companies = pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor",
             "bottleneck_relevance": "high"},
        ])
        monkeypatch.setattr(ret_module, "REF_DIR", tmp_path)
        fake_companies.to_csv(tmp_path / "companies.csv", index=False)

        # load_latest_prices mock
        fake_prices = self._make_price_series(300)
        with patch.object(ret_module, "load_latest_prices", return_value=fake_prices):
            df = ret_module.build_returns_table()

        required_cols = {"ticker", "sector", "ret_1m", "ret_3m"}
        assert required_cols.issubset(df.columns), \
            f"필요 컬럼 누락. 현재: {df.columns.tolist()}"

    def test_load_latest_prices_returns_series_or_none(self, tmp_path, monkeypatch):
        """
        [load_latest_prices]
        데이터 파일이 있으면 pd.Series를 반환해야 한다.
        파일이 없으면 None을 반환해야 한다.
        """
        from src.analysis import returns as ret_module
        monkeypatch.setattr(ret_module, "RAW_DIR", tmp_path)

        # 파일 없는 경우
        result = ret_module.load_latest_prices("FAKE")
        assert result is None, "파일 없으면 None을 반환해야 한다"


# =============================================================================
# ② sector_compare.py
#
# 역할: 수익률 테이블을 집계해서 섹터 성과 비교
#   · load_latest_returns()  → processed/returns/ 에서 가장 최근 CSV 로드
#   · sector_summary(df)     → 섹터별 평균 수익률 테이블 (ret_3m 내림차순)
#   · top_performers(df)     → 지정 기간 상위 n개 기업
#   · bottom_performers(df)  → 지정 기간 하위 n개 기업
# =============================================================================

class TestSectorCompare:

    @pytest.fixture
    def sample_returns(self):
        """테스트용 수익률 DataFrame"""
        return pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA",  "sector": "semiconductor",
             "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0, "ret_6m": 60.0, "ret_1y": 80.0, "ret_ytd": 30.0},
            {"ticker": "AMD",  "company": "AMD",     "sector": "semiconductor",
             "ret_1w": 2.0, "ret_1m": 8.0,  "ret_3m": 20.0, "ret_6m": 30.0, "ret_1y": 40.0, "ret_ytd": 15.0},
            {"ticker": "ETN",  "company": "Eaton",   "sector": "power_equipment",
             "ret_1w": 1.0, "ret_1m": 3.0,  "ret_3m": 10.0, "ret_6m": 15.0, "ret_1y": 20.0, "ret_ytd": 8.0},
            {"ticker": "NEE",  "company": "NextEra", "sector": "power_utility",
             "ret_1w": -1.0, "ret_1m": -2.0, "ret_3m": 5.0, "ret_6m": 8.0,  "ret_1y": 10.0, "ret_ytd": 2.0},
        ])

    def test_sector_summary_has_sector_column(self, sample_returns):
        """
        [sector_summary]
        반환 DataFrame에 sector 컬럼이 있어야 한다.
        각 섹터당 1행이어야 한다.
        """
        from src.analysis.sector_compare import sector_summary
        df = sector_summary(sample_returns)

        assert "sector" in df.columns, "sector 컬럼이 있어야 한다"
        assert df["sector"].nunique() == len(df), "각 섹터당 1행이어야 한다"

    def test_sector_summary_sorted_by_ret_3m(self, sample_returns):
        """
        [sector_summary]
        ret_3m 내림차순으로 정렬되어야 한다.
        """
        from src.analysis.sector_compare import sector_summary
        df = sector_summary(sample_returns)

        ret_3m_vals = df["ret_3m"].tolist()
        assert ret_3m_vals == sorted(ret_3m_vals, reverse=True), \
            "ret_3m 내림차순 정렬이어야 한다"

    def test_top_performers_count(self, sample_returns):
        """
        [top_performers]
        n=2를 넘기면 2개만 반환해야 한다.
        ret_1m 기준 가장 높은 기업들이어야 한다.
        """
        from src.analysis.sector_compare import top_performers
        result = top_performers(sample_returns, n=2, period="ret_1m")

        assert len(result) == 2, "n=2면 2개만 반환해야 한다"
        # 첫 번째가 가장 높아야 함
        assert result.iloc[0]["ret_1m"] >= result.iloc[1]["ret_1m"]

    def test_bottom_performers_count(self, sample_returns):
        """
        [bottom_performers]
        n=2를 넘기면 2개만 반환해야 한다.
        ret_1m 기준 가장 낮은 기업들이어야 한다.
        """
        from src.analysis.sector_compare import bottom_performers
        result = bottom_performers(sample_returns, n=2, period="ret_1m")

        assert len(result) == 2, "n=2면 2개만 반환해야 한다"
        assert result.iloc[0]["ret_1m"] <= result.iloc[1]["ret_1m"]

    def test_load_latest_returns_raises_when_no_file(self, tmp_path, monkeypatch):
        """
        [load_latest_returns]
        processed/returns/ 에 파일이 없으면 FileNotFoundError를 발생시켜야 한다.
        """
        from src.analysis import sector_compare as sc
        monkeypatch.setattr(sc, "PROCESSED_DIR", tmp_path)

        # returns 폴더가 있지만 파일이 없는 경우
        (tmp_path / "returns").mkdir()

        with pytest.raises(FileNotFoundError):
            sc.load_latest_returns()


# =============================================================================
# ③ bottleneck_score.py
#
# 역할: 섹터가 전체 평균 대비 얼마나 강한지 → 병목 점수
#   · load_latest_returns()      → sector_compare.py와 동일 역할
#   · calc_bottleneck_score(df)  → 섹터별 병목 점수 + 신호 레이블
#   · calc_company_momentum(df)  → 기업별 섹터 내 초과 성과
#
# 병목 점수 = 섹터 3M 수익률 - 전체 평균 3M 수익률
# 신호: +10% 초과 → 강한 병목 / +5~10 → 중간 병목 / -5~+5 → 중립 / -5 미만 → 병목 약화
# =============================================================================

class TestBottleneckScore:

    @pytest.fixture
    def sample_returns(self):
        return pd.DataFrame([
            {"ticker": "NVDA", "sector": "semiconductor",   "ret_3m": 50.0, "ret_1m": 15.0, "ret_1w": 3.0},
            {"ticker": "AMD",  "sector": "semiconductor",   "ret_3m": 30.0, "ret_1m": 8.0,  "ret_1w": 1.0},
            {"ticker": "ETN",  "sector": "power_equipment", "ret_3m": 5.0,  "ret_1m": 2.0,  "ret_1w": 0.5},
            {"ticker": "NEE",  "sector": "power_utility",   "ret_3m": -5.0, "ret_1m": -1.0, "ret_1w": -0.5},
        ])

    def test_calc_bottleneck_score_columns(self, sample_returns):
        """
        [calc_bottleneck_score]
        반환 DataFrame에 sector, bottleneck_score, signal 컬럼이 있어야 한다.
        """
        from src.analysis.bottleneck_score import calc_bottleneck_score
        df = calc_bottleneck_score(sample_returns)

        required = {"sector", "bottleneck_score", "signal"}
        assert required.issubset(df.columns), f"필요 컬럼 누락: {required - set(df.columns)}"

    def test_calc_bottleneck_score_sorted_descending(self, sample_returns):
        """
        [calc_bottleneck_score]
        bottleneck_score 내림차순으로 정렬되어야 한다.
        """
        from src.analysis.bottleneck_score import calc_bottleneck_score
        df = calc_bottleneck_score(sample_returns)

        scores = df["bottleneck_score"].tolist()
        assert scores == sorted(scores, reverse=True), "bottleneck_score 내림차순 정렬이어야 한다"

    def test_calc_bottleneck_score_signal_labels(self, sample_returns):
        """
        [calc_bottleneck_score]
        signal 컬럼값이 "강한 병목", "중간 병목", "중립", "병목 약화" 중 하나여야 한다.
        """
        from src.analysis.bottleneck_score import calc_bottleneck_score
        df = calc_bottleneck_score(sample_returns)

        valid_signals = {"강한 병목", "중간 병목", "중립", "병목 약화"}
        for val in df["signal"]:
            assert val in valid_signals, f"유효하지 않은 신호: {val}"

    def test_calc_bottleneck_score_sum_is_zero(self, sample_returns):
        """
        [calc_bottleneck_score]
        bottleneck_score는 (섹터 평균 - 전체 평균)이므로
        가중 평균이 0에 가까워야 한다.
        (모든 섹터 점수 합이 0 근처)
        """
        from src.analysis.bottleneck_score import calc_bottleneck_score
        df = calc_bottleneck_score(sample_returns)

        # company_count 가중 합 ≈ 0
        total = (df["bottleneck_score"] * df["company_count"]).sum()
        assert abs(total) < 1.0, f"가중 합이 0에 가까워야 한다. 현재: {total}"

    def test_calc_company_momentum_columns(self, sample_returns):
        """
        [calc_company_momentum]
        반환 DataFrame에 momentum_vs_sector 컬럼이 추가되어야 한다.
        기업의 ret_3m - 해당 섹터 평균 ret_3m 값이어야 한다.
        """
        from src.analysis.bottleneck_score import calc_company_momentum
        df = calc_company_momentum(sample_returns)

        assert "momentum_vs_sector" in df.columns, "momentum_vs_sector 컬럼이 있어야 한다"

        # semiconductor 평균 = (50 + 30) / 2 = 40
        nvda_row = df[df["ticker"] == "NVDA"].iloc[0]
        assert abs(nvda_row["momentum_vs_sector"] - 10.0) < 0.1, \
            "NVDA: 50 - 40(섹터평균) = 10이어야 한다"


# =============================================================================
# ④ investment_signal.py
#
# 역할: 모멘텀 + 병목 + 밸류에이션 → 종합 투자 신호
#   · percentile_score(series)          → 높을수록 좋은 지표 → 0~10점
#   · inverse_percentile_score(series)  → 낮을수록 좋은 지표(PER 등) → 0~10점
#   · calc_sector_bottleneck_map(df)    → 섹터별 병목 점수 dict (0~10 정규화)
#   · build_investment_signal()         → 최종 투자 신호 DataFrame
#
# 가중치: 모멘텀 40% + 병목 30% + 밸류에이션 30%
# 신호: 8점 이상 → BUY 관심 / 5~8 → WATCH / 5 미만 → NEUTRAL
# =============================================================================

class TestInvestmentSignal:

    def test_percentile_score_range(self):
        """
        [percentile_score]
        반환값이 0~10 사이여야 한다.
        NaN은 5.0(중립)으로 처리되어야 한다.
        """
        from src.analysis.investment_signal import percentile_score
        series = pd.Series([10.0, 20.0, 30.0, float("nan"), 40.0])
        result = percentile_score(series)

        assert result.max() <= 10.0, "최댓값이 10 이하여야 한다"
        assert result.min() >= 0.0, "최솟값이 0 이상이어야 한다"
        assert result.iloc[3] == 5.0, "NaN은 5.0(중립)이어야 한다"

    def test_inverse_percentile_score_order(self):
        """
        [inverse_percentile_score]
        값이 낮을수록 높은 점수를 받아야 한다.
        (PER이 낮으면 밸류에이션 매력적 → 높은 점수)
        """
        from src.analysis.investment_signal import inverse_percentile_score
        series = pd.Series([10.0, 30.0, 50.0])  # 10이 가장 낮은 PER
        result = inverse_percentile_score(series)

        assert result.iloc[0] > result.iloc[2], \
            "낮은 값(10)이 높은 값(50)보다 높은 점수를 받아야 한다"

    def test_calc_sector_bottleneck_map_range(self):
        """
        [calc_sector_bottleneck_map]
        반환 dict의 모든 값이 0~10 사이여야 한다.
        키가 섹터명이어야 한다.
        """
        from src.analysis.investment_signal import calc_sector_bottleneck_map
        df = pd.DataFrame([
            {"ticker": "NVDA", "sector": "semiconductor",   "ret_3m": 50.0},
            {"ticker": "ETN",  "sector": "power_equipment", "ret_3m": 5.0},
            {"ticker": "NEE",  "sector": "power_utility",   "ret_3m": -10.0},
        ])
        result = calc_sector_bottleneck_map(df)

        assert isinstance(result, dict), "dict를 반환해야 한다"
        for sector, score in result.items():
            assert 0.0 <= score <= 10.0, f"{sector}의 점수가 0~10 범위여야 한다. 현재: {score}"

    def test_build_investment_signal_columns(self, tmp_path, monkeypatch):
        """
        [build_investment_signal]
        반환 DataFrame에 ticker, total_score, signal 컬럼이 있어야 한다.
        """
        from src.analysis import investment_signal as inv
        monkeypatch.setattr(inv, "PROCESSED_DIR", tmp_path)
        monkeypatch.setattr(inv, "RAW_DIR", tmp_path)

        fake_returns = pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor",
             "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0, "ret_6m": 60.0, "ret_1y": 80.0, "ret_ytd": 30.0},
        ])
        with patch.object(inv, "load_latest_returns", return_value=fake_returns), \
             patch.object(inv, "load_latest_fundamentals", return_value=None):
            df = inv.build_investment_signal()

        required = {"ticker", "total_score", "signal"}
        assert required.issubset(df.columns), f"필요 컬럼 누락: {required - set(df.columns)}"

    def test_build_investment_signal_signal_values(self, tmp_path, monkeypatch):
        """
        [build_investment_signal]
        signal 컬럼값이 "BUY 관심", "WATCH", "NEUTRAL" 중 하나여야 한다.
        """
        from src.analysis import investment_signal as inv
        monkeypatch.setattr(inv, "PROCESSED_DIR", tmp_path)
        monkeypatch.setattr(inv, "RAW_DIR", tmp_path)

        fake_returns = pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor",
             "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0, "ret_6m": 60.0, "ret_1y": 80.0, "ret_ytd": 30.0},
            {"ticker": "NEE", "company": "NextEra", "sector": "power_utility",
             "ret_1w": -1.0, "ret_1m": -2.0, "ret_3m": -5.0, "ret_6m": -8.0, "ret_1y": -10.0, "ret_ytd": -2.0},
        ])
        with patch.object(inv, "load_latest_returns", return_value=fake_returns), \
             patch.object(inv, "load_latest_fundamentals", return_value=None):
            df = inv.build_investment_signal()

        valid_signals = {"BUY 관심", "WATCH", "NEUTRAL"}
        for val in df["signal"]:
            assert val in valid_signals, f"유효하지 않은 신호: {val}"

    def test_build_investment_signal_sorted_by_total_score(self, tmp_path, monkeypatch):
        """
        [build_investment_signal]
        total_score 내림차순으로 정렬되어야 한다.
        """
        from src.analysis import investment_signal as inv
        monkeypatch.setattr(inv, "PROCESSED_DIR", tmp_path)
        monkeypatch.setattr(inv, "RAW_DIR", tmp_path)

        fake_returns = pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor",
             "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0, "ret_6m": 60.0, "ret_1y": 80.0, "ret_ytd": 30.0},
            {"ticker": "NEE", "company": "NextEra", "sector": "power_utility",
             "ret_1w": -1.0, "ret_1m": -2.0, "ret_3m": -5.0, "ret_6m": -8.0, "ret_1y": -10.0, "ret_ytd": -2.0},
        ])
        with patch.object(inv, "load_latest_returns", return_value=fake_returns), \
             patch.object(inv, "load_latest_fundamentals", return_value=None):
            df = inv.build_investment_signal()

        scores = df["total_score"].tolist()
        assert scores == sorted(scores, reverse=True), "total_score 내림차순이어야 한다"


# =============================================================================
# ⑤ signal_logger.py
#
# 역할: 신호 판단, CSV 기록, 정확도 리뷰
#   · _check_q1(score_trend_4w)         → 추세 방향 체크 ("PASS"/"FAIL")
#   · _check_q2(weeks_since_breakout)   → 돌파 신선도 체크 (8주 이내)
#   · _check_q3(sector_3m, spy_3m)      → 매크로 분리 체크 (5%p 초과)
#   · determine_signal(...)             → Q1~Q4 종합 → 최종 신호 코드
#   · log_signal(...)                   → 신호 계산 + signal_log.csv 1행 추가
#   · log_validation(...)               → 사후 검증 결과 signal_validation.csv 추가
#   · review_accuracy(last_n_weeks)     → 정확도 통계 dict 반환
#   · print_review(last_n_weeks)        → review_accuracy 결과 출력
#   · _append_row(path, row, columns)   → CSV에 1행 추가 (파일 없으면 생성)
# =============================================================================

class TestSignalLogger:

    def test_check_q1_pass_when_positive_trend(self):
        """
        [_check_q1]
        score_trend_4w > 0 이면 "PASS"를 반환해야 한다.
        """
        from src.analysis.signal_logger import _check_q1
        assert _check_q1(5.0) == "PASS", "양의 추세면 PASS"
        assert _check_q1(-1.0) == "FAIL", "음의 추세면 FAIL"
        assert _check_q1(0.0) == "FAIL", "0이면 FAIL (strict >)"

    def test_check_q2_pass_within_8_weeks(self):
        """
        [_check_q2]
        weeks_since_breakout <= 8 이면 "PASS", None이거나 8 초과면 "FAIL".
        """
        from src.analysis.signal_logger import _check_q2
        assert _check_q2(1) == "PASS", "1주 경과 → PASS"
        assert _check_q2(8) == "PASS", "8주 경과 → PASS (경계값 포함)"
        assert _check_q2(9) == "FAIL", "9주 경과 → FAIL"
        assert _check_q2(None) == "FAIL", "None(임계값 미초과) → FAIL"

    def test_check_q3_pass_when_outperform_spy(self):
        """
        [_check_q3]
        sector_3m - spy_3m > 5.0 이면 "PASS".
        """
        from src.analysis.signal_logger import _check_q3
        assert _check_q3(15.0, 5.0) == "PASS", "10%p 초과 → PASS"
        assert _check_q3(10.0, 5.0) == "PASS", "5%p 초과 → PASS"
        assert _check_q3(10.0, 5.1) == "FAIL", "4.9%p → FAIL (strict >)"

    def test_determine_signal_returns_dict_with_keys(self):
        """
        [determine_signal]
        반환값이 dict이고 q1_trend, q2_fresh, q3_macro_sep, q4_physical, final_signal 키가 있어야 한다.
        """
        from src.analysis.signal_logger import determine_signal
        result = determine_signal(
            score_v1=12.0,
            score_trend_4w=3.0,
            weeks_since_breakout=4,
            sector_3m=20.0,
            spy_3m=5.0,
            q4_physical="PASS",
        )

        required_keys = {"q1_trend", "q2_fresh", "q3_macro_sep", "q4_physical", "final_signal"}
        assert required_keys == set(result.keys()), f"키 불일치: {set(result.keys())}"

    def test_determine_signal_strong_buy(self):
        """
        [determine_signal]
        모든 Q가 PASS이고 score_v1 >= 10 이면 STRONG_BUY여야 한다.
        """
        from src.analysis.signal_logger import determine_signal
        result = determine_signal(
            score_v1=12.0,       # >= 10
            score_trend_4w=3.0,  # Q1 PASS
            weeks_since_breakout=4,  # Q2 PASS (4<=8)
            sector_3m=20.0,      # Q3 PASS (20-5=15 > 5)
            spy_3m=5.0,
            q4_physical="PASS",
        )
        assert result["final_signal"] == "STRONG_BUY", \
            f"STRONG_BUY여야 하는데 {result['final_signal']}이 나옴"

    def test_determine_signal_neutral(self):
        """
        [determine_signal]
        모든 조건이 불리할 때 NEUTRAL이어야 한다.
        """
        from src.analysis.signal_logger import determine_signal
        result = determine_signal(
            score_v1=-5.0,
            score_trend_4w=-2.0,
            weeks_since_breakout=None,
            sector_3m=2.0,
            spy_3m=5.0,
            q4_physical="FAIL",
        )
        assert result["final_signal"] in {
            "NEUTRAL", "MONITOR", "MACRO_CAUTION"
        }, f"불리한 조건 → 보수적 신호여야 한다. 현재: {result['final_signal']}"

    def test_log_signal_appends_to_csv(self, tmp_path, monkeypatch):
        """
        [log_signal]
        호출 후 signal_log.csv에 1행이 추가되어야 한다.
        반환값이 dict여야 한다.
        """
        from src.analysis import signal_logger as sl
        monkeypatch.setattr(sl, "SIGNAL_LOG_PATH", tmp_path / "signal_log.csv")

        result = sl.log_signal(
            week_date="2026-03-31",
            sector="semiconductor",
            score_v1=12.0,
            score_trend_4w=3.0,
            weeks_since_breakout=4,
            spy_3m_return=5.0,
            sector_3m_return=20.0,
            avg_3m_return=15.0,
            q4_physical="PASS",
        )

        assert isinstance(result, dict), "log_signal()은 dict를 반환해야 한다"
        df = pd.read_csv(tmp_path / "signal_log.csv")
        assert len(df) == 1, "signal_log.csv에 1행이 추가되어야 한다"

    def test_log_validation_appends_to_csv(self, tmp_path, monkeypatch):
        """
        [log_validation]
        호출 후 signal_validation.csv에 1행이 추가되어야 한다.
        """
        from src.analysis import signal_logger as sl
        monkeypatch.setattr(sl, "VALIDATION_PATH", tmp_path / "signal_validation.csv")

        result = sl.log_validation(
            signal_date="2026-01-01",
            sector="semiconductor",
            original_signal="STRONG_BUY",
            return_4w=8.5,
            return_8w=15.2,
            outcome="CORRECT",
        )

        df = pd.read_csv(tmp_path / "signal_validation.csv")
        assert len(df) == 1, "signal_validation.csv에 1행이 추가되어야 한다"

    def test_review_accuracy_no_file(self, tmp_path, monkeypatch):
        """
        [review_accuracy]
        signal_validation.csv가 없으면 {"error": ...} dict를 반환해야 한다.
        예외가 터지면 안 된다.
        """
        from src.analysis import signal_logger as sl
        monkeypatch.setattr(sl, "VALIDATION_PATH", tmp_path / "no_file.csv")

        result = sl.review_accuracy()
        assert "error" in result, "파일 없을 때 error 키가 있어야 한다"

    def test_review_accuracy_overall_accuracy_range(self, tmp_path, monkeypatch):
        """
        [review_accuracy]
        overall_accuracy가 0~100 사이여야 한다.
        """
        from src.analysis import signal_logger as sl
        monkeypatch.setattr(sl, "VALIDATION_PATH", tmp_path / "val.csv")

        # 가짜 validation 데이터 생성
        sl.log_validation(
            signal_date="2026-01-01",
            sector="semiconductor",
            original_signal="STRONG_BUY",
            return_4w=8.5,
            return_8w=15.2,
            outcome="CORRECT",
        )
        result = sl.review_accuracy()

        assert "overall_accuracy" in result
        assert 0 <= result["overall_accuracy"] <= 100

    def test_append_row_creates_file_if_not_exists(self, tmp_path):
        """
        [_append_row]
        파일이 없으면 헤더와 함께 새로 생성해야 한다.
        """
        from src.analysis.signal_logger import _append_row
        path = tmp_path / "test.csv"
        columns = ["a", "b", "c"]
        row = {"a": 1, "b": 2, "c": 3}

        _append_row(path, row, columns)

        assert path.exists(), "파일이 생성되어야 한다"
        df = pd.read_csv(path)
        assert list(df.columns) == columns
        assert len(df) == 1
