# Resume System — 사용 가이드

## 기본 흐름

```
오늘 한 일 기록
daily_logs/
      ↓
      ├─ generate_bullets.py  → bullets/          (이력서용 bullet)
      ├─ update_resume.py     → resume/            (이력서 초안)
      ├─ build_portfolio.py   → portfolio/         (포트폴리오 문서)
      └─ make_blog_draft.py   → blog_drafts/       (블로그 초안)
```

---

## 매일 할 일 (2분)

```bash
# 1. 오늘 날짜 로그 파일 생성
cp templates/daily_log_template.md daily_logs/$(date +%Y-%m-%d).md

# 2. 편집기에서 오늘 한 일 채우기
# (오늘 한 일 / 사용한 기술 / 어려웠던 점 / 결과·임팩트)

# 3. bullet 생성
cd resume_system
python scripts/generate_bullets.py
```

---

## 이력서 업데이트할 때 (필요할 때만)

```bash
python scripts/update_resume.py
# → resume/master_resume.md 자동 업데이트
```

---

## 포트폴리오 문서 만들 때

```bash
python scripts/build_portfolio.py
# → portfolio/portfolio_AI인프라_병목_분석_시스템.md 생성

python scripts/build_portfolio.py --project "프로젝트명"
# → 특정 프로젝트명으로 생성
```

출력 내용: 한 줄 소개 / 목표 / 사용 기술 / 진행 단계 / 해결한 문제 / 다음 개선점 / 배운 것

---

## 블로그 초안 만들 때

```bash
python scripts/make_blog_draft.py
# → blog_drafts/2026-03-15_draft.md (오늘 날짜, 서술형 400~700자)

python scripts/make_blog_draft.py 2026-03-13
# → 특정 날짜

python scripts/make_blog_draft.py --week
# → blog_drafts/2026-03-09~2026-03-15_weekly_draft.md (주간 회고, 700~1200자)
```

---

## 밀린 로그 한 번에 처리

```bash
python scripts/generate_bullets.py --all
# → 아직 처리 안 된 날짜 전부 처리 (중복 없음)
```

---

## 특정 날짜만 재처리

```bash
python scripts/generate_bullets.py 2026-03-13
```

---

## 파일 구조

```
resume_system/
├── daily_logs/          ← 매일 여기에 YYYY-MM-DD.md 작성
├── bullets/
│   ├── master_bullets.md          ← 전체 bullet 모음
│   └── by_category/
│       ├── data_analysis.md
│       ├── automation.md
│       └── investment_research.md
├── resume/
│   └── master_resume.md           ← 최종 이력서 초안
├── portfolio/           ← build_portfolio.py 출력
├── blog_drafts/         ← make_blog_draft.py 출력
├── scripts/
│   ├── generate_bullets.py        ← 로그 → bullet 변환 (Claude API)
│   ├── update_resume.py           ← bullet → 이력서 섹션 재구성
│   ├── build_portfolio.py         ← 로그 전체 → 포트폴리오 문서
│   └── make_blog_draft.py         ← 로그 → 블로그 초안 (서술형)
└── templates/
    └── daily_log_template.md      ← 매일 이걸 복사해서 씀
```

---

## 주의사항

- `daily_logs/` 파일명은 반드시 `YYYY-MM-DD.md` 형식
- 템플릿의 `YYYY-MM-DD` 제목을 실제 날짜로 바꿔야 처리됨 (안 바꾸면 스킵)
- `ANTHROPIC_API_KEY` 환경변수 설정 필요 (`export ANTHROPIC_API_KEY=sk-...`)
