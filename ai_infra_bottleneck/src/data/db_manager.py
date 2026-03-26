"""
db_manager.py
주가 데이터를 SQLite DB에 저장하고 조회하는 함수 모음.

DB 위치: data/db/ai_infra.db
테이블:
    - prices: 일별 주가 데이터 (ticker, date, open, high, low, close, volume)
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_DIR = Path(__file__).resolve().parents[2] / "data" / "db"
DB_PATH = DB_DIR / "ai_infra.db"


def get_connection() -> sqlite3.Connection:
    """DB 연결을 반환한다. DB 파일이 없으면 자동 생성된다."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """prices 테이블이 없으면 생성한다."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                ticker  TEXT    NOT NULL,
                date    TEXT    NOT NULL,
                open    REAL,
                high    REAL,
                low     REAL,
                close   REAL,
                volume  INTEGER,
                PRIMARY KEY (ticker, date)
            )
        """)
    print(f"[DB] 초기화 완료: {DB_PATH}")


def save_prices(ticker: str, df: pd.DataFrame) -> None:
    """
    yfinance로 받은 DataFrame을 prices 테이블에 저장한다.
    이미 존재하는 (ticker, date) 행은 덮어쓴다 (REPLACE).

    Args:
        ticker: 티커 (예: "NVDA")
        df: yfinance DataFrame (index = date, columns = Open/High/Low/Close/Volume)
    """
    df_db = df.copy()
    df_db.index = pd.to_datetime(df_db.index).strftime("%Y-%m-%d")
    # yfinance 최신 버전은 MultiIndex 컬럼 반환 — 첫 번째 레벨(컬럼명)만 추출
    if isinstance(df_db.columns, pd.MultiIndex):
        df_db.columns = [c[0].lower() for c in df_db.columns]
    else:
        df_db.columns = [c.lower() for c in df_db.columns]
    df_db = df_db[["open", "high", "low", "close", "volume"]]
    df_db.insert(0, "ticker", ticker)
    df_db.index.name = "date"
    df_db = df_db.reset_index()

    with get_connection() as conn:
        df_db.to_sql("prices", conn, if_exists="append", index=False, method=_replace_on_conflict)

    print(f"[DB] {ticker}: {len(df_db)}행 저장")


def _replace_on_conflict(table, conn, keys, data_iter):
    """PRIMARY KEY 충돌 시 REPLACE로 덮어쓰는 커스텀 insert 메서드."""
    placeholders = ", ".join(["?"] * len(keys))
    sql = f"INSERT OR REPLACE INTO {table.name} ({', '.join(keys)}) VALUES ({placeholders})"
    conn.executemany(sql, data_iter)


def load_prices(ticker: str = None, start_date: str = None) -> pd.DataFrame:
    """
    prices 테이블에서 데이터를 조회한다.

    Args:
        ticker: 특정 티커만 조회 (None이면 전체)
        start_date: 이 날짜 이후 데이터만 조회 (예: "2026-01-01")

    Returns:
        DataFrame (columns: ticker, date, open, high, low, close, volume)
    """
    query = "SELECT * FROM prices WHERE 1=1"
    params = []

    if ticker:
        query += " AND ticker = ?"
        params.append(ticker)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    query += " ORDER BY ticker, date"

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def load_sector_avg(start_date: str = None) -> pd.DataFrame:
    """
    섹터별 평균 종가를 조회한다.
    companies.csv의 sector 정보와 JOIN하지 않고,
    호출하는 쪽에서 sector 매핑 후 groupby하는 방식으로 사용.

    Returns:
        DataFrame (columns: ticker, date, close)
    """
    query = "SELECT ticker, date, close FROM prices WHERE 1=1"
    params = []

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    query += " ORDER BY ticker, date"

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


if __name__ == "__main__":
    init_db()
    print(f"[DB] 경로: {DB_PATH}")
