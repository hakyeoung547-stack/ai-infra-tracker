#!/bin/bash
# run_weekly.sh — 매주 월요일 실행: 수익률 계산 + 주간 리포트 생성
# crontab: 0 8 * * 1 /full/path/to/scripts/run_weekly.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/logs/cron.log"

mkdir -p "$PROJECT_DIR/logs"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === weekly report start ===" >> "$LOG_FILE"

source "$PROJECT_DIR/.venv/bin/activate"
python "$PROJECT_DIR/src/analysis/returns.py" >> "$LOG_FILE" 2>&1
python "$PROJECT_DIR/src/reports/weekly_report.py" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === weekly report done ===" >> "$LOG_FILE"
