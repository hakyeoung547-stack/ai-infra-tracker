# ai-infra-tracker

> AI 인프라 밸류체인(반도체·전력·냉각) 섹터 모멘텀을 추적하고, 자동화 파이프라인으로 주간 리포트를 생성하는 개인 분석 프로젝트.

---

## 프로젝트 목표

| 트랙 | 목표 |
|------|------|
| 투자 학습 | AI 인프라 산업 구조 이해 → 섹터별 모멘텀 추적 → 유망 기업 판단 능력 |
| 스킬 구축 | 데이터 엔지니어링 + 자동화 파이프라인 + 시각화 포트폴리오 |

---

## 현재 진행 단계

- [x] Phase 0 — 프로젝트 구조 설계
- [ ] **Phase 1** — 주가 기반 섹터 모멘텀 트래커 + 동적 인프라 맵 시각화 (진행 중)
  - [ ] 주가 수집 자동화 (yfinance → CSV)
  - [ ] 섹터별 수익률·모멘텀 계산
  - [ ] 동적 인프라 맵 (NetworkX + Streamlit)
  - [ ] 주간 리포트 자동 생성 (Markdown)
- [ ] Phase 2 — SEC EDGAR API 재무 데이터 + 공급 제약 신호 통합
- [ ] Phase 3 — Airflow 고도화 + 백테스팅
- [ ] Phase 4 — 네트워크·클라우드·REITs 확장

---

## 분석 대상 기업 (Phase 1)

| 섹터 | 기업 |
|------|------|
| semiconductor | NVDA, AMD, TSM, AMAT, LRCX |
| power_equipment | ETN, SMCI |
| power_utility | NEE, CEG, ETR, PWR |
| cooling | VRT, MOD |

---

## 폴더 구조

```
aI_auto/                          # 레포 루트
├── ai_infra_bottleneck/          # AI 인프라 트래커 메인 프로젝트
│   ├── data/
│   │   ├── raw/          # 원본 데이터 (수정 금지)
│   │   ├── processed/    # 전처리 완료 데이터
│   │   ├── reference/    # companies.csv 등 기준 데이터 (수동 관리)
│   │   └── db/           # SQLite DB (gitignore)
│   ├── src/
│   │   ├── data/         # fetch_prices.py, fetch_fundamentals.py
│   │   ├── analysis/     # returns.py, bottleneck_score.py, sector_compare.py
│   │   ├── visualization/# infra_map.py
│   │   └── reports/      # weekly_report.py
│   ├── notebooks/        # 탐색·실험용 Jupyter Notebook
│   ├── docs/             # 분석 프레임워크, 투자 논리 문서
│   ├── reports/          # 자동 생성된 주간·섹터 리포트
│   └── scripts/          # run_daily.sh, run_weekly.sh
├── resume_system/                # 이력서 자동화 시스템 (별도 트랙)
└── CLAUDE.md                     # Claude Code용 프로젝트 가이드
```

---

## 실행 방법

```bash
# 환경 설정
python -m venv .venv
source .venv/bin/activate
pip install -r ai_infra_bottleneck/requirements.txt

# 주가 데이터 수집
python ai_infra_bottleneck/src/data/fetch_prices.py

# 수익률 계산
python ai_infra_bottleneck/src/analysis/returns.py

# 섹터 비교
python ai_infra_bottleneck/src/analysis/sector_compare.py

# 병목 점수 계산
python ai_infra_bottleneck/src/analysis/bottleneck_score.py
```

---

## 기술 스택

- **데이터 수집**: yfinance, SEC EDGAR API (Phase 2)
- **데이터 처리**: pandas, numpy
- **시각화**: matplotlib, plotly, NetworkX, pyvis, Streamlit
- **자동화**: cron → Apache Airflow (Phase 3)
- **리포트**: Jinja2 + Markdown

---

## 작업 히스토리

| 날짜 | 내용 |
|------|------|
| 2026-03-13 | 프로젝트 구조 설계, CLAUDE.md 초안 |
| 2026-03-13 | 병목 분석 3단계 프레임워크 완성 |
| 2026-03-16 | 프로젝트 방향 재정의, infra_map.py 스켈레톤 생성 |
| 2026-03-25 | 데이터 소스 이중 구조 확정 (yfinance + SEC EDGAR) |
| 2026-03-26 | GitHub 초기 설정, Git 버전 관리 시작 |
