"""
update_all.py
cron 진입점. 전체 데이터를 순서대로 업데이트한다.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

SRC_DIR = Path(__file__).resolve().parent


def run(script: str) -> None:
    print(f"\n{'='*40}")
    print(f"실행: {script} — {datetime.now().strftime('%H:%M:%S')}")
    result = subprocess.run([sys.executable, str(SRC_DIR / script)], check=True)
    print(f"완료: {script}")


if __name__ == "__main__":
    print(f"[START] 데이터 업데이트 시작 — {datetime.now()}")
    run("fetch_prices.py")
    run("fetch_fundamentals.py")
    print(f"\n[DONE] 모든 업데이트 완료 — {datetime.now()}")
