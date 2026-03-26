# Bullets — Automation & Engineering

> generate_bullets.py가 자동 분류해서 추가함

---

## 2026-03-21

- 파이썬 데코레이터 작동 원리 체득 — 함수를 변수처럼 다루고 바꿔치기하는 구조 이해
- `*args / **kwargs` 묶기·풀기 메커니즘 학습 및 실무 패턴 적용 완료
- Claude API 툴 등록 패턴(`@register` 데코레이터 + `**kwargs` 전달) 직접 구현 및 검증
- 완성형 wrapper 표준 구조 확립: `def wrapper(*args, **kwargs): return func(*args, **kwargs)`
- wrapper형(실행 변형) vs 등록형(목록 관리) 데코레이터 2종류 분류 및 각 실무 사례 정리
- 자동화 파이프라인에서 `return` 누락 시 결과 소실 문제 직접 확인 및 해결 패턴 정리
