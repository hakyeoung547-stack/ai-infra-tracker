"""
build_portfolio.py

daily_logs/ 전체를 읽어서
프로젝트별로 "무엇을 왜 만들었고, 어떻게 발전했는가"를
구조적으로 정리한 포트폴리오 문서를 생성한다.

출력: portfolio/portfolio_{프로젝트명}.md

사용법:
    python scripts/build_portfolio.py
    python scripts/build_portfolio.py --project ai_infra   # 특정 프로젝트만
"""

import sys
from pathlib import Path
from datetime import date
import anthropic

ROOT = Path(__file__).parent.parent
DAILY_LOGS = ROOT / "daily_logs"
PORTFOLIO_DIR = ROOT / "portfolio"

SYSTEM_PROMPT = """당신은 개발자/분석가의 일일 작업 로그를 바탕으로 포트폴리오 문서를 작성하는 전문가입니다.

주어진 로그들을 분석해서 아래 구조로 포트폴리오 문서를 작성하세요.

---

# {프로젝트명}

## 한 줄 소개
프로젝트가 해결하는 핵심 문제를 한 문장으로.

## 목표
이 프로젝트로 무엇을 달성하려 했는가.

## 사용 기술
로그에서 언급된 기술/도구를 실제 사용 맥락과 함께. 단순 나열 말고 "무엇을 위해 사용했는지" 포함.

## 진행 단계
날짜 순서로 프로젝트가 어떻게 발전했는지.
형식: YYYY-MM-DD | 한 일 요약

## 해결한 문제
로그에서 "어려웠던 점 / 해결 방법" 항목을 바탕으로 실제로 부딪혀서 해결한 문제들.

## 다음 개선점
로그의 "내일 할 일" 또는 미완성 부분을 바탕으로 앞으로 발전시킬 방향.

## 이 프로젝트에서 배운 것
기술적 성장 + 사고방식 변화 포함.

---

규칙:
- 과장하지 말 것. 로그에 실제로 있는 내용만 사용.
- 진행 단계는 날짜별로 구체적으로.
- 마크다운 형식으로 반환."""


def collect_all_logs() -> str:
    logs = sorted(DAILY_LOGS.glob("*.md"))
    if not logs:
        print("daily_logs/에 로그 파일이 없습니다.")
        sys.exit(1)

    combined = []
    for log in logs:
        content = log.read_text().strip()
        if "YYYY-MM-DD" in content:
            continue
        combined.append(f"=== {log.stem} ===\n{content}")

    return "\n\n".join(combined)


def build_portfolio(project_name: str, logs_content: str) -> str:
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"프로젝트명: {project_name}\n\n아래는 이 프로젝트 관련 일일 작업 로그입니다:\n\n{logs_content}"
            }
        ]
    )

    return message.content[0].text


def main():
    args = sys.argv[1:]
    project_name = None
    for i, a in enumerate(args):
        if a == "--project" and i + 1 < len(args):
            project_name = args[i + 1]

    if not project_name:
        project_name = "AI 인프라 병목 분석 시스템"

    print(f"프로젝트: {project_name}")
    print("로그 수집 중...")

    logs_content = collect_all_logs()
    log_count = logs_content.count("=== 20")
    print(f"로그 {log_count}개 수집 완료. 포트폴리오 생성 중...")

    portfolio = build_portfolio(project_name, logs_content)

    safe_name = project_name.replace(" ", "_").replace("/", "-")
    output_path = PORTFOLIO_DIR / f"portfolio_{safe_name}.md"
    output_path.write_text(portfolio)

    print(f"\n저장 완료: {output_path.relative_to(ROOT)}")
    print("\n--- 미리보기 ---")
    print(portfolio[:600])
    if len(portfolio) > 600:
        print("... (이하 생략)")


if __name__ == "__main__":
    main()
