#!/bin/bash
# setup.sh — venv 생성 및 패키지 설치

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== AI 인프라 병목 분석 프로젝트 환경 설정 ==="
echo "경로: $PROJECT_DIR"

# venv 생성
python3 -m venv .venv
echo "[OK] venv 생성 완료"

# 패키지 설치
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "[OK] 패키지 설치 완료"

# .env 파일 생성 안내
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[INFO] .env 파일을 생성했습니다. 필요한 경우 API 키를 입력하세요."
fi

echo ""
echo "=== 설정 완료 ==="
echo "환경 활성화: source .venv/bin/activate"
echo "데이터 수집: python src/data/update_all.py"
echo "주간 리포트: python src/reports/weekly_report.py"
