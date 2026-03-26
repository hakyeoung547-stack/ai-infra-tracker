#!/bin/bash
# run_daily.sh — 매일 실행: 주가 데이터 업데이트
# crontab: 0 7 * * 1-5 /full/path/to/scripts/run_daily.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/logs/cron.log"

mkdir -p "$PROJECT_DIR/logs"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === daily update start ===" >> "$LOG_FILE"

source "$PROJECT_DIR/.venv/bin/activate"
python "$PROJECT_DIR/src/data/update_all.py" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === daily update done ===" >> "$LOG_FILE"
