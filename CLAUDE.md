# AI 인프라 섹터 트래커 — CLAUDE.md

> 이 파일은 Claude Code가 이 프로젝트를 이해하고 작업하기 위한 핵심 가이드다.
> 프로젝트가 확장될 때마다 이 파일을 업데이트한다.

---

## 프로젝트 한 줄 정의

AI 인프라 밸류체인(반도체·전력·냉각)에 속한 기업들의 섹터 모멘텀을 추적하고,
동적 인프라 맵으로 시각화하여 **투자 공부 + 데이터 엔지니어링 스킬 구축**을 동시에 하는 개인 분석 프로젝트.

### 두 가지 목표

| 트랙 | 목표 | 현재 단계에서 하는 것 |
|------|------|----------------------|
| **투자 학습** | AI 인프라 산업 구조 이해 → 유망 기업 판단 능력 쌓기 | 섹터별 모멘텀 추적, 어닝콜 직접 읽기, 맵으로 흐름 파악 |
| **스킬 구축** | 데이터 엔지니어링 + 자동화 파이프라인 + 시각화 포트폴리오 | 데이터 수집 자동화, 주간 리포트 생성, 인프라 맵 대시보드 |

### 솔직한 현재 범위

Phase 1에서 실제로 쓰는 데이터는 **yfinance 주가 데이터**뿐이다.
지금 이 시스템이 하는 건 정확히 말하면 **섹터 모멘텀 비교 + 자동화 리포트 + 인프라 맵 시각화**다.
"병목 분석"의 핵심인 수주잔고·납기 데이터는 Phase 2에서 어닝콜을 직접 읽으며 수동으로 채운다.

---

## 현재 단계

- [x] Phase 0: 프로젝트 구조 설계 (CLAUDE.md, 폴더 구조)
- [ ] Phase 1: 주가 기반 섹터 모멘텀 트래커 + 동적 인프라 맵 시각화
  - [ ] 1-1: 주가 수집 자동화 (yfinance → CSV)
  - [ ] 1-2: 섹터별 수익률·모멘텀 계산
  - [ ] 1-3: 동적 인프라 맵 (NetworkX + Streamlit — 모멘텀으로 노드 강조)
  - [ ] 1-4: 주간 리포트 자동 생성 (Markdown)
- [ ] Phase 2: 재무 데이터 추가 + 공급 제약 신호 통합
  - SEC EDGAR API로 수주잔고·영업이익·book-to-bill 자동 수집 (`fetch_edgar.py`)
  - 어닝콜 직접 읽고 납기 지연·수주잔고 메모 → 시스템에 수동 보완 입력
- [ ] Phase 3: 자동화 고도화 (Airflow) + 백테스팅
- [ ] Phase 4: 네트워크·클라우드·REITs 확장

---

## 폴더 구조

```
ai_infra_bottleneck/
│
├── CLAUDE.md                        ← 이 파일. 프로젝트 전체 가이드
├── README.md                        ← 외부 공개용 프로젝트 소개
├── requirements.txt                 ← pip 패키지 목록
├── .env.example                     ← API 키 예시 (실제 .env는 gitignore)
├── .gitignore
│
├── data/
│   ├── raw/                         ← 원본 데이터. 수정 금지. 항상 보존
│   │   ├── prices/                  ← yfinance로 받은 주가 CSV (ticker_YYYYMMDD.csv)
│   │   └── fundamentals/            ← PER, PSR 등 재무 데이터 (ticker_fundamentals.csv)
│   ├── processed/                   ← 전처리 완료 데이터 (분석에 직접 사용)
│   │   ├── returns/                 ← 수익률 계산 결과
│   │   └── metrics/                 ← 변동성, 샤프지수 등 지표
│   └── reference/                   ← 직접 만드는 기준 데이터 (수동 관리)
│       ├── companies.csv            ← 핵심 기업 분류 마스터 테이블
│       └── sector_weights.csv       ← 섹터 가중치 정의 (선택)
│
├── src/                             ← 실제 Python 코드
│   ├── data/
│   │   ├── fetch_prices.py          ← yfinance로 주가 수집
│   │   ├── fetch_fundamentals.py    ← 재무 데이터 수집
│   │   └── update_all.py            ← 전체 데이터 일괄 업데이트 (cron 진입점)
│   │
│   ├── analysis/
│   │   ├── returns.py               ← 수익률 계산 (1W/1M/3M/6M/1Y)
│   │   ├── volatility.py            ← 변동성, 최대낙폭(MDD) 계산
│   │   ├── correlation.py           ← 섹터 간 상관관계 분석
│   │   ├── sector_compare.py        ← 섹터별 성과 비교 테이블 생성
│   │   ├── bottleneck_score.py      ← 병목 지수 계산 (1단계: 점수 계산)
│   │   └── signal_quality.py        ← 신호 품질 체크 (2단계: Q1추세·Q2신선도·Q3매크로·Q4실물)
│   │
│   ├── visualization/
│   │   ├── charts.py                ← matplotlib/plotly 차트 생성 함수 모음
│   │   └── infra_map.py             ← AI 인프라 구조도 시각화
│   │
│   └── reports/
│       ├── weekly_report.py         ← 주간 Markdown 리포트 자동 생성
│       ├── sector_report.py         ← 섹터별 심층 리포트 생성
│       └── templates/
│           ├── weekly_template.md   ← 주간 리포트 템플릿
│           └── sector_template.md   ← 섹터 리포트 템플릿
│
├── notebooks/                       ← 탐색/실험용 Jupyter Notebook
│   ├── 01_data_exploration.ipynb    ← 데이터 확인 및 초기 탐색
│   ├── 02_sector_returns.ipynb      ← 섹터별 수익률 분석
│   ├── 03_bottleneck_analysis.ipynb ← 병목 분석 실험
│   └── 04_company_deep_dive.ipynb   ← 개별 기업 심층 분석
│
├── reports/                         ← 자동 생성된 리포트 저장소
│   ├── weekly/                      ← YYYY-WW_weekly.md 형식
│   ├── sector/                      ← sector_power_YYYYMM.md 형식
│   └── bottleneck/                  ← bottleneck_YYYYMM.md 형식
│
├── docs/                            ← 수동으로 작성하는 분석 문서
│   ├── industry_map.md              ← AI 인프라 밸류체인 구조 정리
│   ├── bottleneck_framework.md      ← 병목 분석 프레임워크 설명
│   ├── sector_power.md              ← 전력 섹터 기업 분석
│   ├── sector_cooling.md            ← 냉각 섹터 기업 분석
│   ├── sector_semiconductor.md      ← 반도체 섹터 기업 분석
│   └── investment_thesis.md         ← 종합 투자 논리 정리
│
└── scripts/                         ← 실행 자동화 쉘 스크립트
    ├── setup.sh                     ← venv 생성 + 패키지 설치
    ├── run_daily.sh                 ← 매일: 데이터 업데이트
    └── run_weekly.sh                ← 매주: 리포트 생성
```

---

## 핵심 데이터: data/reference/companies.csv

이 프로젝트의 중심이 되는 마스터 데이터셋.
모든 분석은 이 파일을 기준으로 돌아간다.

### 컬럼 정의

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| ticker | 주식 티커 | NVDA |
| company | 기업명 | NVIDIA |
| sector | 대분류 섹터 | semiconductor |
| sub_sector | 세부 분류 | gpu_design |
| exchange | 상장 거래소 | NASDAQ |
| country | 국가 | US |
| bottleneck_relevance | 병목 연관도 (high/mid/low) | high |
| supply_side | 공급 측면 역할 (Y/N) | Y |
| demand_driver | 수요 창출 역할 (Y/N) | N |
| phase | 분석 단계 (1/2/3) | 1 |
| notes | 투자 포인트 메모 | GPU 공급 독점적 위치 |

### sector 허용값 (확장 시 추가)
- `semiconductor` — GPU, 칩 설계, 파운드리
- `power_equipment` — 변압기, 배전, UPS, 전력 관리
- `power_utility` — 발전, 전력 공급, 송전망
- `cooling` — 액체/공기 냉각, 열 관리
- `network` — 데이터센터 내 고속 통신, 스위치
- `cloud` — 클라우드 플랫폼, AI 서비스
- `datacenter_reit` — 데이터센터 부동산

### Phase 1 기업 목록 (초기 설정값)

| ticker | company | sector | sub_sector |
|--------|---------|--------|------------|
| NVDA | NVIDIA | semiconductor | gpu_design |
| AMD | AMD | semiconductor | gpu_design |
| TSM | TSMC | semiconductor | foundry |
| AMAT | Applied Materials | semiconductor | equipment |
| LRCX | Lam Research | semiconductor | equipment |
| NEE | NextEra Energy | power_utility | renewable |
| CEG | Constellation Energy | power_utility | nuclear |
| ETR | Entergy | power_utility | utility |
| ETN | Eaton | power_equipment | power_mgmt |
| SMCI | Super Micro Computer | power_equipment | server_power |
| PWR | Quanta Services | power_utility | grid_infra |
| VRT | Vertiv | cooling | liquid_cooling |
| MOD | Modine Manufacturing | cooling | thermal_mgmt |

---

## 언어 규칙

### resume_system/ 파일 작성 언어
- `resume_system/` 폴더 안의 **모든 파일은 반드시 한국어로 작성**한다.
  - `resume/master_resume.md` — 한국어
  - `bullets/master_bullets.md` — 한국어
  - `daily_logs/*.md` — 한국어
  - `blog_drafts/*.md` — 한국어
- 영어 혼용 금지. 기술 용어(Python, async, pandas 등)는 그대로 쓰되, 설명·bullet 문장은 한국어로 작성.

---

## 코드 규칙

### Python 환경
- **가상환경**: venv (`python -m venv .venv`)
- **활성화**: `source .venv/bin/activate`
- **패키지 추가 후**: `pip freeze > requirements.txt` 업데이트

### 핵심 패키지
```
yfinance          # 주가 데이터 수집
pandas            # 데이터 처리
numpy             # 수치 계산
matplotlib        # 정적 차트
plotly            # 인터랙티브 차트
python-dotenv     # 환경변수 관리
schedule          # 스케줄링 (필요 시)
jinja2            # 리포트 템플릿 렌더링
networkx          # 인프라 맵 그래프 구조 (노드·엣지 정의)
pyvis             # NetworkX → 인터랙티브 HTML 시각화
streamlit         # 인프라 맵 대시보드 웹앱
```

### 파일 네이밍 규칙
- Python 모듈: `snake_case.py`
- 데이터 파일: `{ticker}_{YYYYMMDD}.csv` (원본), `{name}_{YYYYMM}.csv` (처리본)
- 리포트: `{YYYY}-W{WW}_weekly.md`, `sector_{name}_{YYYYMM}.md`
- 노트북: `{NN}_{topic}.ipynb` (숫자 prefix로 순서 표시)

### 코드 스타일
- 함수는 단일 책임 원칙. 하나의 함수는 하나의 일만 한다.
- 데이터프레임 변수명: `df_` prefix 사용 (예: `df_prices`, `df_returns`)
- 날짜 형식: 항상 `YYYY-MM-DD` 문자열 또는 `datetime` 객체
- 경로: `pathlib.Path` 사용, 하드코딩 금지

### data/ 폴더 규칙
- `data/raw/`는 절대 수정하지 않는다. 원본 보존.
- 전처리는 항상 `data/processed/`에 새 파일로 저장.
- `data/reference/companies.csv`는 수동 관리. 스크립트로 덮어쓰지 않는다.

---

## 분석 프레임워크

### 병목 판단 기준 — 3단계 체계

단순 점수 하나로 판단하지 않는다. 반드시 3단계를 거친다.
상세 기준은 `docs/bottleneck_framework.md` 참고.

#### 1단계: 병목 점수 계산

3가지 신호를 조합:
1. **가격 모멘텀** — 섹터 3M/6M 상대 수익률 (현재 구현)
2. **공급 제약** — 납기 지연, 수주잔고, 어닝콜 키워드 (Phase 2 구현)
3. **수요 압력** — 빅테크 CAPEX 증가율과 섹터 수익률 상관관계 (Phase 2 구현)

```
# 현재 버전 (v1 — 모멘텀만)
bottleneck_score_v1 = 섹터_3M_수익률 - 전체_AI인프라_평균_3M_수익률

# 목표 버전 (v2 — 3신호 통합)
bottleneck_score_v2 = (모멘텀_점수 * 0.4) + (공급제약_점수 * 0.3) + (수요압력_점수 * 0.3)
```

#### 2단계: 신호 품질 체크 (4가지)

점수가 나오면 반드시 아래 4가지를 확인한다:

| 체크 항목 | 확인 방법 | 관련 코드 |
|-----------|-----------|-----------|
| Q1. 추세 방향 | 지난 4주 점수 변화 (상승/하락) | `signal_quality.py` |
| Q2. 돌파 신선도 | 이번 주 처음 임계값 돌파인가? | `signal_quality.py` |
| Q3. 매크로 분리 | SPY도 같이 움직였는가? | `rel_to_spy` 지표 활용 |
| Q4. 실물 근거 | 납기/수주잔고/어닝콜 뒷받침 | Phase 2 이후 자동화 |

#### 3단계: 최종 판단 매트릭스

1+2단계 결과 조합 → 8가지 신호 중 하나로 결론:

| 신호 | 의미 | 행동 |
|------|------|------|
| 🔴 강한 병목 신호 | 점수↑, 첫 돌파, 섹터 독자, 실물 확인 | 적극 검토 |
| 🟡 매크로 랠리 주의 | 점수↑, 첫 돌파, SPY도 상승 | 실물 확인 후 판단 |
| ⛔ 고점 경계 | 점수 수개월 지속 또는 하락 전환 | 신규 진입 금지 |
| 🟠 모니터링 강화 | +5~10%, 상승 중, 부분 확인 | 진입 준비 단계 |
| 🟢 선취매 검토 | 중립이지만 서서히 상승, 선행 신호 | 조용히 진입 가능 |
| ⚪ 중립 관망 | 중립, 횡보, 특별한 신호 없음 | 관망 |
| 🔵 섹터 교체 신호 | 점수 하락, SPY 멀쩡, 실물 약화 | 비중 축소 |
| 🟢 역발상 구간 | 점수 하락, SPY도 하락, 펀더멘탈 유지 | 장기 보유 또는 매수 |

### 섹터 비교 분석 지표

매주 자동 계산하는 지표:

| 지표 | 설명 | 3단계 활용 |
|------|------|------------|
| ret_1w | 1주 수익률 | — |
| ret_1m | 1개월 수익률 | — |
| ret_3m | 3개월 수익률 | **1단계 점수 계산 기준** |
| ret_ytd | 연초 대비 수익률 | — |
| vol_30d | 30일 연환산 변동성 | — |
| mdd | 최대낙폭 (Maximum Drawdown) | — |
| sharpe | 샤프 지수 (무위험 수익률 4.5% 기준) | — |
| rel_to_spy | SPY 대비 상대 수익률 | **2단계 Q3 매크로 분리 확인** |
| rel_to_soxx | SOXX(반도체 ETF) 대비 상대 수익률 | — |
| score_trend_4w | 4주간 점수 변화 추세 | **2단계 Q1 추세 방향 확인** |
| breakout_fresh | 이번 주 임계값 첫 돌파 여부 (bool) | **2단계 Q2 돌파 신선도 확인** |

**공급 제약 신호 지표** (Phase 2 구현 예정 — 분기별 어닝 데이터 기반)

| 지표 | 설명 | 수집 방법 |
|------|------|-----------|
| backlog | 수주잔고 절대값 (억 달러) | SEC EDGAR API (`RevenueRemainingPerformanceObligation`) → 없으면 어닝 리포트 수동 |
| backlog_qoq | 수주잔고 전분기 대비 증가율 | backlog 계산 파생 |
| book_to_bill | 신규 수주 / 납품액 비율 (1.0 초과 = 병목 심화) | 어닝 리포트 수동 수집 (XBRL 미표준) |
| dc_order_ratio | 전체 수주 중 데이터센터 고객 비중 (%) | 어닝 리포트 수동 수집 |
| lead_time_signal | 납기 지연 언급 여부 (1/0) | 어닝콜 키워드 추출 (Phase 3 자동화) |
| margin_trend | 영업이익률 추세 | SEC EDGAR API (`OperatingIncomeLoss`) — 자동 수집 가능 |

---

## 자동화 구조 (cron)

### crontab 설정 위치
```
crontab -e  # 편집
crontab -l  # 확인
```

### 권장 cron 스케줄
```bash
# 매일 오전 7시: 주가 데이터 업데이트
0 7 * * 1-5 /path/to/project/scripts/run_daily.sh

# 매주 월요일 오전 8시: 주간 리포트 생성
0 8 * * 1 /path/to/project/scripts/run_weekly.sh
```

### 스크립트 구조
```bash
# run_daily.sh
#!/bin/bash
cd /path/to/ai_infra_bottleneck
source .venv/bin/activate
python src/data/update_all.py
echo "[$(date)] Daily update done" >> logs/cron.log

# run_weekly.sh
#!/bin/bash
cd /path/to/ai_infra_bottleneck
source .venv/bin/activate
python src/reports/weekly_report.py
echo "[$(date)] Weekly report done" >> logs/cron.log
```

---

## 리포트 구조

### 주간 리포트 (reports/weekly/YYYY-WW_weekly.md)

```
# AI 인프라 주간 리포트 — {날짜}

## 이번 주 요약
- 전체 AI 인프라 지수: {수익률}
- 섹터 중 최고 성과: {섹터} ({수익률})
- 주목할 변화: ...

## 섹터별 주간 성과
{섹터 비교 테이블}

## 병목 신호 변화
{bottleneck_score 변화}

## 주요 기업 동향
{상위 5개 기업 수익률 + 메모}

## 다음 주 관찰 포인트
- ...
```

---

## 확장 계획

### Phase 2 추가 예정 섹터
- `network`: Arista Networks (ANET), Broadcom (AVGO), Marvell (MRVL)
- `cloud`: Microsoft (MSFT), Amazon (AMZN), Alphabet (GOOGL)
- `datacenter_reit`: Equinix (EQIX), Digital Realty (DLR)

### Phase 3 고도화 항목
- 어닝콜 텍스트 키워드 분석 (공급 제약 신호 추출)
- 뉴스 헤드라인 자동 수집 및 감성 분석
- 인프라 맵 대시보드 Streamlit 배포 (Community Cloud)
- Apache Airflow 기반 파이프라인 전환
- 매크로 변수(전력 선물가격, 반도체 PMI 등)와 주가 상관관계 분석
- AI 인프라 종합 지수 자체 구성

---

## 자주 쓰는 명령어

```bash
# 환경 활성화
source .venv/bin/activate

# 데이터 업데이트
python src/data/update_all.py

# 주간 리포트 생성
python src/reports/weekly_report.py

# 특정 섹터 분석 실행
python src/analysis/sector_compare.py --sector power

# 노트북 실행
jupyter notebook notebooks/
```

---

## 작업 히스토리

| 날짜 | 작업 내용 |
|------|-----------|
| 2026-03-13 | 프로젝트 구조 설계, CLAUDE.md 초안 작성 |
| 2026-03-13 | bottleneck_framework.md 3단계 판단 프레임워크 완성 (판단기준표 + 신호품질체크 + 최종매트릭스), CLAUDE.md 분석 프레임워크 섹션 업데이트 |
| 2026-03-16 | 프로젝트 방향 재정의 — 두 트랙(투자 학습 + 스킬 구축) 명시, Phase 1 솔직한 스코프(섹터 모멘텀 + 동적 인프라 맵)로 업데이트, infra_map.py 스켈레톤 생성, networkx·pyvis·streamlit 추가 |
| 2026-03-25 | 데이터 소스 이중 구조 확정 — yfinance(주가·모멘텀, Phase 1) + SEC EDGAR API(수주잔고·마진·실물, Phase 2), Phase 2 설명 업데이트, 공급 제약 지표 수집 방법 SEC EDGAR 기준으로 수정, docs/api_guide.md에 SEC EDGAR 섹션 추가 |

> 작업할 때마다 이 테이블에 한 줄씩 추가한다.
