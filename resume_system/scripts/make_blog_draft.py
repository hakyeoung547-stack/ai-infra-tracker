"""
make_blog_draft.py

하루 로그를 읽어서 사람이 읽을 수 있는 블로그 초안을 생성한다.
bullet이 아니라 서술형 글 형태.

예시 출력:
  "오늘은 왜 로그 구조를 통일해야 하는지 깨달았다"
  "병목을 주가가 아니라 수주잔고로 먼저 보는 시각을 정리했다"

출력: blog_drafts/YYYY-MM-DD_draft.md

사용법:
    python scripts/make_blog_draft.py               # 오늘 날짜
    python scripts/make_blog_draft.py 2026-03-13    # 특정 날짜
    python scripts/make_blog_draft.py --week        # 최근 7일치 묶어서 한 편
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import anthropic

ROOT = Path(__file__).parent.parent
DAILY_LOGS = ROOT / "daily_logs"
BLOG_DIR = ROOT / "blog_drafts"

SYSTEM_PROMPT = """당신은 개발자/분석가의 일일 작업 로그를 바탕으로 블로그 초안을 쓰는 작가입니다.

규칙:
1. 독자는 비슷한 수준의 개발자/분석가. 너무 쉽게 설명하지 않아도 됨.
2. 서술형으로 쓴다. bullet point 금지.
3. "오늘 깨달은 것" 또는 "오늘 해결한 문제" 중심으로 서사를 만든다.
4. 기술 설명보다 "왜 이렇게 했는가", "무엇을 배웠는가"에 집중.
5. 길이: 400~700자 (한국어 기준). 너무 길지 않게.
6. 제목 1개 + 본문으로 구성.
7. 마지막 문장은 "다음에는 ~을 해볼 생각이다" 또는 "~가 궁금해졌다" 형태로 마무리.
8. 과장하거나 없는 내용 추가하지 말 것.

형식:
# {제목}

{본문}
"""

WEEKLY_SYSTEM_PROMPT = """당신은 개발자/분석가의 일주일 작업 로그를 바탕으로 주간 회고 블로그 초안을 쓰는 작가입니다.

규칙:
1. 일주일 동안 있었던 일을 하나의 흐름으로 연결해서 서술.
2. 하루하루 요약이 아니라 "이번 주에 무엇이 달라졌는가"를 중심으로.
3. 기술적 성장 + 사고방식 변화 포함.
4. 서술형. bullet 금지.
5. 길이: 700~1200자.
6. 제목 1개 + 소제목 2~3개 + 본문.

형식:
# {주간 회고 제목}

## {소제목1}
{내용}

## {소제목2}
{내용}
"""


def get_log(target_date: str) -> str | None:
    log_path = DAILY_LOGS / f"{target_date}.md"
    if not log_path.exists():
        return None
    content = log_path.read_text().strip()
    if "YYYY-MM-DD" in content:
        return None
    return content


def get_week_logs() -> tuple[str, str]:
    today = date.today()
    logs = []
    dates = []
    for i in range(6, -1, -1):
        d = str(today - timedelta(days=i))
        content = get_log(d)
        if content:
            logs.append(f"=== {d} ===\n{content}")
            dates.append(d)

    if not logs:
        print("최근 7일 내 로그 없음.")
        sys.exit(1)

    label = f"{dates[0]} ~ {dates[-1]}"
    return "\n\n".join(logs), label


def make_single_draft(log_date: str) -> str:
    content = get_log(log_date)
    if not content:
        print(f"로그 없음: {log_date}")
        sys.exit(1)

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"날짜: {log_date}\n\n작업 로그:\n{content}"
            }
        ]
    )
    return message.content[0].text


def make_weekly_draft(logs_content: str) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        system=WEEKLY_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"아래는 이번 주 일일 작업 로그입니다:\n\n{logs_content}"
            }
        ]
    )
    return message.content[0].text


def main():
    args = sys.argv[1:]
    is_week = "--week" in args
    target_date = next((a for a in args if a != "--week"), None)

    if is_week:
        print("최근 7일 로그로 주간 회고 생성 중...")
        logs_content, label = get_week_logs()
        draft = make_weekly_draft(logs_content)
        output_path = BLOG_DIR / f"{label}_weekly_draft.md"
    else:
        log_date = target_date or str(date.today())
        print(f"{log_date} 블로그 초안 생성 중...")
        draft = make_single_draft(log_date)
        output_path = BLOG_DIR / f"{log_date}_draft.md"

    output_path.write_text(draft)

    print(f"\n저장 완료: {output_path.relative_to(ROOT)}")
    print("\n--- 초안 미리보기 ---")
    print(draft[:500])
    if len(draft) > 500:
        print("... (이하 생략)")


if __name__ == "__main__":
    main()
