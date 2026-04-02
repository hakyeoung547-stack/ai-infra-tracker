"""
=============================================================================
STEP 1 — 데이터 수집 레이어 (src/data/)
=============================================================================

실행 순서:
  ① db_manager.py     → DB 연결 & 테이블 초기화
  ② fetch_prices.py   → 주가 수집 & CSV + DB 저장
  ③ fetch_fundamentals.py → 밸류에이션 지표 수집 & CSV 저장
  ④ update_all.py     → ②③을 순서대로 자동 실행하는 cron 진입점

이 파일의 모든 테스트는 현재 RED(실패) 상태입니다.
구현이 완료되면 GREEN으로 바뀌어야 합니다.
"""

import pytest
import pandas as pd
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# 프로젝트 루트를 import path에 추가
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# =============================================================================
# ① db_manager.py
#
# 역할: SQLite DB와의 모든 대화를 담당하는 창구
#   · get_connection()  → DB 파일에 연결 (없으면 자동 생성)
#   · init_db()         → prices 테이블이 없으면 CREATE TABLE
#   · save_prices()     → yfinance DataFrame을 prices 테이블에 UPSERT
#   · load_prices()     → prices 테이블 조회 (ticker / start_date 필터 지원)
#   · load_sector_avg() → ticker, date, close 컬럼만 가볍게 조회
# =============================================================================

class TestDbManager:

    def test_get_connection_returns_sqlite_connection(self):
        """
        [get_connection]
        DB 파일이 없어도 연결 객체를 반환해야 한다.
        반환 타입이 sqlite3.Connection인지 확인.
        """
        from src.data.db_manager import get_connection
        conn = get_connection()
        assert isinstance(conn, sqlite3.Connection), \
            "get_connection()은 sqlite3.Connection을 반환해야 한다"
        conn.close()

    def test_init_db_creates_prices_table(self, tmp_path, monkeypatch):
        """
        [init_db]
        호출 후 prices 테이블이 존재해야 한다.
        prices 테이블의 컬럼: ticker, date, open, high, low, close, volume
        """
        from src.data import db_manager
        # tmp DB 경로로 교체
        monkeypatch.setattr(db_manager, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(db_manager, "DB_DIR", tmp_path)

        db_manager.init_db()

        conn = sqlite3.connect(tmp_path / "test.db")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "init_db() 후 prices 테이블이 존재해야 한다"

    def test_save_prices_inserts_rows(self, tmp_path, monkeypatch):
        """
        [save_prices]
        yfinance 스타일 DataFrame을 넘기면 prices 테이블에 행이 저장되어야 한다.
        PRIMARY KEY(ticker, date) 충돌 시 REPLACE로 덮어써야 한다.
        """
        from src.data import db_manager
        monkeypatch.setattr(db_manager, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(db_manager, "DB_DIR", tmp_path)
        db_manager.init_db()

        # yfinance가 반환하는 형태의 가짜 DataFrame
        idx = pd.to_datetime(["2026-03-01", "2026-03-02"])
        df = pd.DataFrame({
            "Open":   [100.0, 101.0],
            "High":   [105.0, 106.0],
            "Low":    [99.0,  100.0],
            "Close":  [103.0, 104.0],
            "Volume": [1000,  1100],
        }, index=idx)

        db_manager.save_prices("NVDA", df)

        conn = sqlite3.connect(tmp_path / "test.db")
        rows = conn.execute("SELECT * FROM prices WHERE ticker='NVDA'").fetchall()
        conn.close()

        assert len(rows) == 2, "2행이 저장되어야 한다"

    def test_load_prices_returns_dataframe(self, tmp_path, monkeypatch):
        """
        [load_prices]
        조회 결과가 pandas DataFrame이어야 한다.
        ticker 필터 없이 호출하면 전체 데이터를 반환해야 한다.
        """
        from src.data import db_manager
        monkeypatch.setattr(db_manager, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(db_manager, "DB_DIR", tmp_path)
        db_manager.init_db()

        df = db_manager.load_prices()
        assert isinstance(df, pd.DataFrame), "load_prices()는 DataFrame을 반환해야 한다"

    def test_load_prices_ticker_filter(self, tmp_path, monkeypatch):
        """
        [load_prices] ticker 필터
        ticker="NVDA"를 넘기면 NVDA 데이터만 반환해야 한다.
        다른 티커 데이터가 섞여선 안 된다.
        """
        from src.data import db_manager
        monkeypatch.setattr(db_manager, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(db_manager, "DB_DIR", tmp_path)
        db_manager.init_db()

        # NVDA, AAPL 두 개 저장
        for ticker, price in [("NVDA", 500.0), ("AAPL", 200.0)]:
            idx = pd.to_datetime(["2026-03-01"])
            df = pd.DataFrame({
                "Open": [price], "High": [price], "Low": [price],
                "Close": [price], "Volume": [1000],
            }, index=idx)
            db_manager.save_prices(ticker, df)

        result = db_manager.load_prices(ticker="NVDA")
        assert all(result["ticker"] == "NVDA"), "NVDA만 반환해야 한다"
        assert "AAPL" not in result["ticker"].values

    def test_load_sector_avg_columns(self, tmp_path, monkeypatch):
        """
        [load_sector_avg]
        반환 DataFrame에 ticker, date, close 컬럼이 있어야 한다.
        """
        from src.data import db_manager
        monkeypatch.setattr(db_manager, "DB_PATH", tmp_path / "test.db")
        monkeypatch.setattr(db_manager, "DB_DIR", tmp_path)
        db_manager.init_db()

        df = db_manager.load_sector_avg()
        assert set(["ticker", "date", "close"]).issubset(df.columns), \
            "load_sector_avg()는 ticker, date, close 컬럼을 포함해야 한다"


# =============================================================================
# ② fetch_prices.py
#
# 역할: yfinance로 주가를 가져와서 CSV + DB에 동시 저장
#   · load_tickers()   → companies.csv에서 티커 목록 읽기
#   · fetch_prices()   → yfinance API 호출, {ticker: DataFrame} 반환
#   · save_prices()    → CSV 파일 + DB 동시 저장
# =============================================================================

class TestFetchPrices:

    def test_load_tickers_returns_list(self):
        """
        [load_tickers]
        반환값이 리스트여야 한다.
        비어있지 않아야 한다 (companies.csv에 최소 1개 이상의 티커가 있다).
        """
        from src.data.fetch_prices import load_tickers
        tickers = load_tickers()
        assert isinstance(tickers, list), "load_tickers()는 list를 반환해야 한다"
        assert len(tickers) > 0, "티커 목록이 비어있으면 안 된다"

    def test_load_tickers_all_strings(self):
        """
        [load_tickers]
        모든 티커가 문자열이어야 한다.
        """
        from src.data.fetch_prices import load_tickers
        tickers = load_tickers()
        assert all(isinstance(t, str) for t in tickers), "모든 티커가 str이어야 한다"

    def test_fetch_prices_returns_dict(self):
        """
        [fetch_prices]
        반환값이 {str: DataFrame} 딕셔너리여야 한다.
        빈 티커 리스트를 넘기면 빈 딕셔너리를 반환해야 한다.
        """
        from src.data.fetch_prices import fetch_prices
        result = fetch_prices([])
        assert isinstance(result, dict), "fetch_prices()는 dict를 반환해야 한다"
        assert result == {}, "빈 입력이면 빈 딕셔너리여야 한다"

    def test_fetch_prices_single_ticker_mocked(self):
        """
        [fetch_prices]
        yfinance를 mock해서 실제 네트워크 없이 테스트.
        결과 dict에 해당 티커 키가 있어야 한다.
        DataFrame이어야 한다.
        """
        from src.data.fetch_prices import fetch_prices

        fake_df = pd.DataFrame({"Close": [100.0, 101.0]})

        with patch("src.data.fetch_prices.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = fake_df
            result = fetch_prices(["NVDA"])

        assert "NVDA" in result, "NVDA 키가 결과에 있어야 한다"
        assert isinstance(result["NVDA"], pd.DataFrame)

    def test_fetch_prices_skips_empty_dataframe(self):
        """
        [fetch_prices]
        yfinance가 빈 DataFrame을 반환하면 해당 티커를 결과에서 제외해야 한다.
        (데이터 없는 티커를 조용히 건너뜀)
        """
        from src.data.fetch_prices import fetch_prices

        with patch("src.data.fetch_prices.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()
            result = fetch_prices(["FAKE"])

        assert "FAKE" not in result, "빈 DataFrame 티커는 결과에서 제외해야 한다"

    def test_save_prices_creates_csv(self, tmp_path, monkeypatch):
        """
        [save_prices]
        {ticker: DataFrame} 딕셔너리를 넘기면
        data/raw/prices/{TICKER}_{YYYYMMDD}.csv 파일이 생성되어야 한다.
        """
        from src.data import fetch_prices as fp
        monkeypatch.setattr(fp, "RAW_DIR", tmp_path)

        # DB 저장은 mock 처리
        with patch("src.data.fetch_prices.db_save_prices"):
            idx = pd.to_datetime(["2026-03-01"])
            fake_df = pd.DataFrame({
                "Open": [100.0], "High": [105.0], "Low": [99.0],
                "Close": [103.0], "Volume": [1000],
            }, index=idx)
            fp.save_prices({"NVDA": fake_df})

        csv_files = list(tmp_path.glob("NVDA_*.csv"))
        assert len(csv_files) == 1, "NVDA_{날짜}.csv 파일이 생성되어야 한다"


# =============================================================================
# ③ fetch_fundamentals.py
#
# 역할: yfinance .info에서 밸류에이션 지표를 수집해서 CSV 저장
#   · load_tickers()       → companies.csv에서 티커 목록
#   · fetch_fundamentals() → {ticker + FIELDS} DataFrame 반환
#   · save_fundamentals()  → fundamentals_{YYYYMMDD}.csv 저장
# =============================================================================

class TestFetchFundamentals:

    EXPECTED_FIELDS = [
        "trailingPE", "forwardPE", "priceToSales", "priceToBook",
        "marketCap", "revenueGrowth", "grossMargins", "returnOnEquity",
    ]

    def test_fetch_fundamentals_columns(self):
        """
        [fetch_fundamentals]
        반환 DataFrame에 ticker + 8개 FIELDS 컬럼이 모두 있어야 한다.
        """
        from src.data.fetch_fundamentals import fetch_fundamentals, FIELDS

        fake_info = {f: 1.0 for f in FIELDS}

        with patch("src.data.fetch_fundamentals.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = fake_info
            df = fetch_fundamentals(["NVDA"])

        assert "ticker" in df.columns, "ticker 컬럼이 있어야 한다"
        for field in self.EXPECTED_FIELDS:
            assert field in df.columns, f"{field} 컬럼이 있어야 한다"

    def test_fetch_fundamentals_none_for_missing(self):
        """
        [fetch_fundamentals]
        yfinance .info에 없는 필드는 None으로 채워져야 한다.
        (KeyError가 나면 안 됨)
        """
        from src.data.fetch_fundamentals import fetch_fundamentals

        with patch("src.data.fetch_fundamentals.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = {}  # 아무 필드도 없는 경우
            df = fetch_fundamentals(["NVDA"])

        assert df.loc[0, "forwardPE"] is None or pd.isna(df.loc[0, "forwardPE"]), \
            "없는 필드는 None/NaN이어야 한다"

    def test_save_fundamentals_creates_csv(self, tmp_path, monkeypatch):
        """
        [save_fundamentals]
        DataFrame을 넘기면 fundamentals_{YYYYMMDD}.csv 파일이 생성되어야 한다.
        """
        from src.data import fetch_fundamentals as ff
        monkeypatch.setattr(ff, "RAW_DIR", tmp_path)

        df = pd.DataFrame([{"ticker": "NVDA", "forwardPE": 30.0}])
        ff.save_fundamentals(df)

        csv_files = list(tmp_path.glob("fundamentals_*.csv"))
        assert len(csv_files) == 1, "fundamentals_{날짜}.csv가 생성되어야 한다"
