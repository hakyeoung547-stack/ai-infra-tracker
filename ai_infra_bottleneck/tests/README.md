# TDD 테스트 가이드 — ai_infra_bottleneck

## 전체 파이프라인 실행 순서

```
STEP 1: 데이터 수집
  scripts/run_daily.sh (매일 07:00)
  └─ src/data/update_all.py
      ├─ src/data/db_manager.py   ← DB 초기화
      ├─ src/data/fetch_prices.py ← 주가 수집 + 저장
      └─ src/data/fetch_fundamentals.py ← 밸류에이션 수집

STEP 2: 분석
  scripts/run_weekly.sh (매주 월 08:00)
  └─ src/analysis/returns.py         ← 수익률 계산
  └─ src/reports/weekly_report.py
      ├─ src/analysis/sector_compare.py    ← 섹터 비교
      ├─ src/analysis/bottleneck_score.py  ← 병목 점수
      ├─ src/analysis/investment_signal.py ← 투자 신호
      └─ src/analysis/signal_logger.py     ← 신호 기록

STEP 3: 리포트 & 시각화
  └─ reports/weekly/{YYYY-WXX}_weekly.md 생성
  └─ streamlit run src/visualization/infra_map.py
```

## 테스트 실행법 (Claude Code 터미널)

```bash
# 전체 실행
cd /Volumes/G-DRIVE\ mobile/aI_auto/ai_infra_bottleneck
python -m pytest tests/ -v

# STEP별 실행
python -m pytest tests/test_step1_data.py -v
python -m pytest tests/test_step2_analysis.py -v
python -m pytest tests/test_step3_reports_viz.py -v

# 특정 클래스만
python -m pytest tests/test_step1_data.py::TestDbManager -v

# 특정 테스트만
python -m pytest tests/test_step2_analysis.py::TestSignalLogger::test_check_q1_pass_when_positive_trend -v
```

## 현재 테스트 상태

```
53 passed, 6 skipped (2026-04-03 기준)
```

- 6 skipped = infra_map.py pyvis 관련 (의도적 스킵)

## TDD 사이클

1. **RED** → 테스트 먼저 작성, 실패 확인
2. **GREEN** → 함수 구현 후 테스트 통과
3. **REFACTOR** → 코드 정리 (테스트는 계속 통과)

## 파일 구조

```
tests/
├── __init__.py
├── test_step1_data.py       ← db_manager, fetch_prices, fetch_fundamentals
├── test_step2_analysis.py   ← returns, sector_compare, bottleneck_score,
│                               investment_signal, signal_logger
└── test_step3_reports_viz.py ← weekly_report, infra_map
```
