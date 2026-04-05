# AI 인프라 섹터 트래커

> AI 인프라 밸류체인(반도체·전력·냉각) 섹터 모멘텀을 추적하고, Streamlit 대시보드와 자동화 파이프라인으로 주간 리포트를 생성하는 개인 분석 프로젝트.

---

## 프로젝트 목표

| 트랙 | 목표 |
|------|------|
| 투자 학습 | AI 인프라 산업 구조 이해 → 섹터별 모멘텀 추적 → 유망 기업 판단 능력 |
| 스킬 구축 | 데이터 엔지니어링 + 자동화 파이프라인 + 시각화 포트폴리오 |

---

## 현재 진행 단계

- [x] Phase 0 — 프로젝트 구조 설계
- [x] **Phase 1** — 주가 기반 섹터 모멘텀 트래커 + 동적 인프라 맵 시각화 ✅
  - [x] 주가 수집 자동화 (yfinance → CSV + SQLite)
  - [x] 섹터별 수익률·모멘텀 계산 + 병목 점수
  - [x] 동적 인프라 맵 (NetworkX + pyvis + Streamlit 4탭 대시보드)
  - [x] 주간 리포트 자동 생성 (Jinja2 + Markdown)
  - [x] crontab 자동화 (매일 07:00 수집 / 매주 월 08:00 리포트)
  - [x] TDD 테스트 스위트 (53 passed)
- [ ] Phase 2 — SEC EDGAR API 재무 데이터 + 공급 제약 신호 통합
- [ ] Phase 3 — Airflow 고도화 + 백테스팅 + HuggingFace FinBERT 어닝콜 분석
- [ ] Phase 4 — 네트워크·클라우드·REITs 확장

---

## 대시보드 실행

```bash
cd ai_infra_bottleneck
source .venv/bin/activate
streamlit run src/visualization/infra_map.py
```

브라우저에서 `http://localhost:8501` 접속

### 대시보드 구성

| 탭 | 내용 |
|----|------|
| 📊 섹터 모멘텀 | 섹터별 수익률 바차트 + 기간별 라인차트 + 컬러 테이블 |
| 🔥 병목 점수 | 병목 점수 수평 바차트 + 🔴🟠⚪🔵 신호 테이블 |
| 🏢 기업별 모멘텀 | 섹터 필터 + 기업별 수익률 + 바차트 |
| 🗺️ 인프라 맵 | pyvis 인터랙티브 공급망 네트워크 |

---

## 분석 대상 기업 (Phase 1 — 13개)

| 섹터 | 기업 |
|------|------|
| semiconductor | NVDA, AMD, TSM, AMAT, LRCX |
| power_equipment | ETN, SMCI |
| power_utility | NEE, CEG, ETR, PWR |
| cooling | VRT, MOD |

---

## 폴더 구조

```
aI_auto/
├── ai_infra_bottleneck/
│   ├── src/
│   │   ├── data/           # fetch_prices.py, db_manager.py, update_all.py
│   │   ├── analysis/       # returns.py, bottleneck_score.py, sector_compare.py
│   │   │                   # investment_signal.py, signal_logger.py
│   │   ├── visualization/  # infra_map.py (Streamlit 대시보드)
│   │   └── reports/        # weekly_report.py
│   ├── tests/              # TDD 테스트 스위트 (53 passed)
│   ├── data/
│   │   ├── raw/            # 원본 주가 CSV (gitignore)
│   │   ├── processed/      # 수익률 계산 결과 (gitignore)
│   │   ├── reference/      # companies.csv (수동 관리)
│   │   └── db/             # SQLite DB (gitignore)
│   ├── scripts/            # run_daily.sh, run_weekly.sh (cron 자동화)
│   ├── reports/            # 자동 생성 주간 리포트 (gitignore)
│   ├── logs/               # bugfix_log.md, cron.log (gitignore)
│   └── docs/               # 분석 프레임워크, 투자 논리 문서
├── resume_system/          # 이력서 자동화 + 학습 일지
└── CLAUDE.md               # Claude Code용 프로젝트 가이드
```

---

## 실행 방법

```bash
# 1. 환경 설정
cd ai_infra_bottleneck
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 데이터 수집 (전체)
python src/data/update_all.py

# 3. 수익률 계산
python src/analysis/returns.py

# 4. 주간 리포트 생성
python src/reports/weekly_report.py

# 5. 대시보드 실행
streamlit run src/visualization/infra_map.py

# 6. 테스트 실행
python -m pytest tests/ -v
```

### 자동화 (crontab)

```
# 매일 평일 오전 7시 — 주가 데이터 수집
0 7 * * 1-5 /path/to/scripts/run_daily.sh

# 매주 월요일 오전 8시 — 주간 리포트 생성
0 8 * * 1 /path/to/scripts/run_weekly.sh
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| 데이터 수집 | yfinance, SEC EDGAR API (Phase 2) |
| 데이터 처리 | pandas, numpy, SQLite |
| 시각화 | plotly, NetworkX, pyvis, Streamlit |
| 테스트 | pytest (TDD) |
| 리포트 | Jinja2 + Markdown |
| 자동화 | cron → Apache Airflow (Phase 3) |

---

## 작업 히스토리

| 날짜 | 내용 |
|------|------|
| 2026-03-13 | 프로젝트 구조 설계, CLAUDE.md 초안 |
| 2026-03-13 | 병목 분석 3단계 프레임워크 완성 |
| 2026-03-16 | 프로젝트 방향 재정의, infra_map.py 스켈레톤 생성 |
| 2026-03-25 | 데이터 소스 이중 구조 확정 (yfinance + SEC EDGAR) |
| 2026-03-26 | SQLite 레이어 추가, GitHub 초기 설정 |
| 2026-04-03 | **Phase 1 완료** — 대시보드 4탭, 테스트 53 passed, 주간 리포트, crontab 자동화 |
