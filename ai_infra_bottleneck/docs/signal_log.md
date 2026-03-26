# 신호 추적 시스템 — 필드 정의 가이드

> 최초 작성: 2026-03-13
>
> 이 문서는 `data/signals/` 폴더의 두 CSV 파일에 사용되는
> 모든 필드와 코드 값의 정의를 담는다.

---

## 파일 구조

```
data/signals/
├── signal_log.csv         ← 주간 신호 생성 기록
└── signal_validation.csv  ← 신호 결과 검증 기록
```

---

## signal_log.csv — 주간 신호 기록

### 목적

매주 월요일, 전주 데이터를 기반으로 섹터별 병목 신호를 계산하고 기록한다.
이 파일이 쌓이면 병목 신호의 역사를 추적할 수 있다.

### 필드 정의

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `week_date` | YYYY-MM-DD | 해당 주 월요일 날짜 | `2026-03-16` |
| `sector` | string | 분석 섹터 (허용값 아래 참조) | `power_equipment` |
| `score_v1` | float | 섹터 3M 수익률 − AI 인프라 평균 3M 수익률 (%) | `12.3` |
| `score_trend_4w` | float | score_v1 현재 − score_v1 4주 전 (추세) | `3.5` |
| `q1_trend` | PASS/FAIL | score_trend_4w > 0이면 PASS | `PASS` |
| `q2_fresh` | PASS/FAIL | 임계값 초과 후 8주 이내이면 PASS | `PASS` |
| `q3_macro_sep` | PASS/FAIL | 섹터 3M - SPY 3M > 5%이면 PASS | `PASS` |
| `q4_physical` | PASS/FAIL/NA | 수동 입력. 수주잔고 등 확인 | `PASS` |
| `final_signal` | code | 최종 신호 코드 (아래 참조) | `STRONG_BUY` |
| `spy_3m_return` | float | SPY 3개월 수익률 (%) | `8.2` |
| `sector_3m_return` | float | 해당 섹터 3개월 수익률 (%) | `28.5` |
| `avg_3m_return` | float | AI 인프라 전체 평균 3개월 수익률 (%) | `16.2` |

### sector 허용값

| 값 | 설명 |
|----|------|
| `semiconductor` | GPU, 칩 설계, 파운드리, 장비 |
| `power_equipment` | 변압기, PDU, UPS, 전력 관리 |
| `power_utility` | 발전, 전력 공급, 송전망 |
| `cooling` | 액체/공기 냉각, 열 관리 |
| `network` | 데이터센터 내 고속 통신 (Phase 2) |
| `cloud` | 클라우드 플랫폼, AI 서비스 (Phase 2) |
| `datacenter_reit` | 데이터센터 부동산 (Phase 2) |

### final_signal 코드표

| 코드 | 의미 | 발동 조건 |
|------|------|-----------|
| `STRONG_BUY` | 강력 매수 신호 | Q1~Q4 모두 PASS + score_v1 >= 10% |
| `EARLY_ENTRY` | 선행 진입 고려 | Q1~Q3 PASS + Q4 NA/미확인 + score_v1 5~10% |
| `MACRO_CAUTION` | 매크로 주의 | Q1~Q2 PASS + Q3 FAIL (SPY와 동조) |
| `PEAK_WARNING` | 고점 경고 | Q1 FAIL + score_v1 >= 15% (하락 추세) |
| `SECTOR_SWITCH` | 섹터 전환 신호 | 한 섹터 PEAK_WARNING + 다른 섹터 EARLY_ENTRY 동시 |
| `MONITOR` | 관찰 유지 | Q1 PASS + Q2~Q4 중 1개 이상 FAIL |
| `CONTRARIAN` | 역발상 검토 | 모든 지표 부정적 + 수주잔고만 갑자기 증가 |
| `NEUTRAL` | 중립 | 특이 신호 없음 |

---

## signal_validation.csv — 신호 결과 검증

### 목적

`signal_log.csv`에 기록된 신호가 실제로 맞았는지 추적한다.
신호 발생 후 4주, 8주 수익률을 입력하고 결과를 분류한다.
이 파일이 쌓이면 어떤 조건에서 신호가 잘 맞는지/틀리는지 패턴을 발견할 수 있다.

### 필드 정의

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `signal_date` | YYYY-MM-DD | 원래 신호 발생 날짜 | `2026-03-16` |
| `sector` | string | 분석 섹터 | `power_equipment` |
| `original_signal` | code | 당시 기록한 final_signal | `STRONG_BUY` |
| `return_4w` | float | 신호 발생 후 4주 섹터 수익률 (%) | `6.2` |
| `return_8w` | float | 신호 발생 후 8주 섹터 수익률 (%) | `11.5` |
| `outcome` | code | 결과 분류 (아래 참조) | `CORRECT` |
| `error_type` | code | 틀린 경우 오류 유형 (아래 참조) | `—` |
| `q_missed` | code | 놓친 체크 (복수 가능) | `Q3` |
| `threshold_verdict` | code | 임계값 적절성 평가 | `OK` |
| `lesson_tag` | code | 학습 분류 태그 | `GOOD_SIGNAL` |
| `notes` | text | 자유 메모 | `ETN 실적 발표와 맞물림` |

### outcome 코드표

| 코드 | 의미 | 기준 |
|------|------|------|
| `CORRECT` | 신호 방향 맞음 | STRONG_BUY 후 4w 또는 8w 수익률 양수 + SPY 초과 |
| `EARLY` | 방향은 맞지만 4w 수익률 아직 없음 | 8w에는 수익 발생 |
| `LATE` | 이미 반영됐음 | 신호 후 수익률 0 또는 음수 |
| `WRONG_DIR` | 방향 자체가 틀림 | STRONG_BUY 후 8w 수익률 음수 |
| `PARTIAL` | 일부만 맞음 | 수익은 났지만 SPY 초과 안 됨 |
| `NOISE` | 신호 자체가 의미 없었음 | score_v1이 데이터 오류 등으로 인한 착시 |

### error_type 코드표

| 코드 | 의미 | 주로 발생하는 조건 |
|------|------|-------------------|
| `ALREADY_PRICED` | 신호 전에 이미 반영 | Q2(신선도) 실패했을 때 |
| `MACRO_SURPRISE` | 예상 외 금리/환율 충격 | Q3 PASS했지만 갑작스러운 매크로 이벤트 |
| `FALSE_BREAKOUT` | 일시적 돌파 후 되돌림 | Q1 추세가 1~2주만 유지 |
| `PHYSICAL_LAG` | 수주 매출 인식까지 긴 시간 | 전력 섹터에서 흔함 |
| `THRESHOLD_ISSUE` | 임계값이 너무 낮거나 높음 | 다수 WRONG_DIR 발생 시 재검토 |
| `BUBBLE` | 밸류에이션 과열로 급락 | 테마 절정기 |
| `SPY_MISSED` | SPY 강세로 인한 착시 | Q3(매크로 분리) 실패했을 때 |

### q_missed 코드표

| 코드 | 의미 |
|------|------|
| `Q1` | 추세 방향 미확인 |
| `Q2` | 신선도 만료 신호 진입 |
| `Q3` | SPY 동조 현상 무시 |
| `Q4` | 물리적 근거 미확인 |
| `Q34` | Q3와 Q4 동시 누락 |
| `NONE` | 모든 체크 통과했으나 틀림 (진짜 예외) |

### threshold_verdict 코드표

| 코드 | 의미 | 조치 |
|------|------|------|
| `OK` | 임계값 적절함 | 유지 |
| `TOO_HIGH` | 임계값이 높아서 좋은 신호 놓침 | 하향 검토 |
| `TOO_LOW` | 임계값이 낮아서 노이즈 신호 발생 | 상향 검토 |
| `TIMING` | 임계값은 맞지만 타이밍 문제 | 진입 방식 조정 |

### lesson_tag 코드표

| 코드 | 의미 |
|------|------|
| `GOOD_SIGNAL` | 시스템이 잘 작동한 사례 |
| `IMPROVE_Q1` | Q1 체크 강화 필요 |
| `IMPROVE_Q2` | Q2 신선도 기준 조정 필요 |
| `IMPROVE_Q3` | Q3 매크로 분리 기준 조정 필요 |
| `IMPROVE_Q4` | Q4 물리적 근거 확인 강화 필요 |
| `SECTOR_NUANCE` | 섹터 특성 이해 부족 (sub_sector 필요) |
| `TIMING_ISSUE` | 진입/청산 타이밍 조정 필요 |
| `EXTERNAL_SHOCK` | 시스템 외부 변수 (학습 불가) |

---

## 월간 리뷰 쿼리 (Python)

매월 말에 실행해서 시스템 성능을 점검한다.

```python
import pandas as pd

df_log = pd.read_csv('data/signals/signal_log.csv')
df_val = pd.read_csv('data/signals/signal_validation.csv')

# 1. 신호 유형별 정확도
accuracy = df_val.groupby('original_signal')['outcome'].value_counts(normalize=True)
print(accuracy)

# 2. 가장 많이 발생한 오류 유형
error_counts = df_val[df_val['error_type'] != '—']['error_type'].value_counts()
print(error_counts)

# 3. 놓친 체크 빈도
q_missed = df_val[df_val['q_missed'] != 'NONE']['q_missed'].value_counts()
print(q_missed)

# 4. 임계값 문제 여부
threshold_issues = df_val[df_val['threshold_verdict'] != 'OK']['threshold_verdict'].value_counts()
print(threshold_issues)

# 5. 섹터별 신호 정확도
sector_accuracy = df_val.groupby('sector')['outcome'].apply(
    lambda x: (x == 'CORRECT').sum() / len(x)
).sort_values(ascending=False)
print(sector_accuracy)
```

---

## 업데이트 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-03-13 | 초안 작성 |
