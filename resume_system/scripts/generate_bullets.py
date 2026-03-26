"""
generate_bullets.py

daily_logs/ 폴더의 마크다운 파일을 읽어서
Claude API로 이력서용 bullet을 생성하고
bullets/master_bullets.md와 bullets/by_category/ 에 저장한다.

사용법:
    python scripts/generate_bullets.py               # 오늘 날짜 로그 처리
    python scripts/generate_bullets.py 2026-03-13    # 특정 날짜 처리
    python scripts/generate_bullets.py --all         # 미처리 로그 전체 처리
"""

import sys
import json
from pathlib import Path
from datetime import date
import anthropic

ROOT = Path(__file__).parent.parent
DAILY_LOGS = ROOT / "daily_logs"
MASTER_BULLETS = ROOT / "bullets" / "master_bullets.md"
BY_CATEGORY = ROOT / "bullets" / "by_category"
PROCESSED_LOG = ROOT / "bullets" / ".processed.json"  # 이미 처리한 날짜 기록

CATEGORIES = {
    "data_analysis": "데이터 분석, 통계, 시각화, 리서치, 금융 분석, 투자 분석",
    "automation": "자동화, 파이썬 스크립트, 데이터 파이프라인, API, 크론, 엔지니어링",
    "investment_research": "투자 아이디어, 섹터 분석, 병목 분석, 주가, 포트폴리오",
}

SYSTEM_PROMPT = """당신은 데이터 분석가 겸 개발자의 일일 작업 로그를 국내 기업 이력서용 bullet point로 변환하는 전문가입니다.

규칙:
1. 각 bullet은 "동사(명사형 종결) + 대상 + 방법/도구 + 임팩트(숫자 있으면 포함)" 형식으로 작성
   예시: "yfinance 기반 주가 수집 파이프라인 구축 — AI 인프라 13개 기업 일별 자동 수집"
2. 한국어로 작성
3. 명사형으로 끝내기 (예: ~구축, ~개발, ~설계, ~분석, ~자동화)
4. 너무 사소한 것 (파일 이름 변경, 폴더 생성 등)은 bullet으로 만들지 않음
5. 하루 로그에서 최대 3개의 bullet 생성
6. 임팩트 숫자가 없으면 만들어내지 말 것. 있는 것만 포함.

응답은 반드시 아래 JSON 형식으로만 반환:
{
  "bullets": [
    {
      "text": "yfinance 기반 주가 수집 파이프라인 구축 — AI 인프라 4개 섹터 13개 기업 일별 자동 수집",
      "category": "automation"
    }
  ]
}

category는 반드시 "data_analysis", "automation", "investment_research" 중 하나."""


def load_processed() -> set:
    if PROCESSED_LOG.exists():
        return set(json.loads(PROCESSED_LOG.read_text()))
    return set()


def save_processed(processed: set):
    PROCESSED_LOG.write_text(json.dumps(sorted(processed), indent=2))


def get_log_dates_to_process(target_date: str | None, process_all: bool) -> list[Path]:
    if process_all:
        processed = load_processed()
        all_logs = sorted(DAILY_LOGS.glob("*.md"))
        return [p for p in all_logs if p.stem not in processed]

    target = target_date or str(date.today())
    log_path = DAILY_LOGS / f"{target}.md"
    if not log_path.exists():
        print(f"로그 파일 없음: {log_path}")
        print(f"템플릿 복사 후 작성: templates/daily_log_template.md → daily_logs/{target}.md")
        sys.exit(1)
    return [log_path]


def generate_bullets_from_log(log_content: str, log_date: str) -> list[dict]:
    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"날짜: {log_date}\n\n작업 로그:\n{log_content}"
            }
        ]
    )

    response_text = message.content[0].text
    result = json.loads(response_text)
    return result["bullets"]


def append_to_master(bullets: list[dict], log_date: str):
    lines = [f"\n### {log_date}\n"]
    for b in bullets:
        lines.append(f"- {b['text']}\n")

    with open(MASTER_BULLETS, "a") as f:
        f.writelines(lines)


def append_to_category(bullets: list[dict], log_date: str):
    by_cat: dict[str, list[str]] = {}
    for b in bullets:
        cat = b.get("category", "data_analysis")
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(b["text"])

    for cat, cat_bullets in by_cat.items():
        cat_file = BY_CATEGORY / f"{cat}.md"
        if not cat_file.exists():
            cat_file.write_text(f"# Bullets — {cat.replace('_', ' ').title()}\n\n---\n")

        lines = [f"\n### {log_date}\n"]
        for text in cat_bullets:
            lines.append(f"- {text}\n")

        with open(cat_file, "a") as f:
            f.writelines(lines)


def process_log(log_path: Path):
    log_date = log_path.stem
    print(f"\n처리 중: {log_date}")

    log_content = log_path.read_text()

    # 템플릿 그대로면 스킵
    if "YYYY-MM-DD" in log_content:
        print(f"  스킵: 날짜가 채워지지 않은 템플릿")
        return

    bullets = generate_bullets_from_log(log_content, log_date)

    if not bullets:
        print(f"  생성된 bullet 없음 (로그 내용이 부족할 수 있음)")
        return

    append_to_master(bullets, log_date)
    append_to_category(bullets, log_date)

    processed = load_processed()
    processed.add(log_date)
    save_processed(processed)

    print(f"  생성된 bullet {len(bullets)}개:")
    for b in bullets:
        print(f"    [{b['category']}] {b['text'][:60]}...")


def main():
    args = sys.argv[1:]
    process_all = "--all" in args
    target_date = next((a for a in args if a != "--all"), None)

    logs_to_process = get_log_dates_to_process(target_date, process_all)

    if not logs_to_process:
        print("처리할 로그 없음. (이미 전부 처리됨)")
        return

    print(f"처리할 로그: {len(logs_to_process)}개")

    for log_path in logs_to_process:
        process_log(log_path)

    print("\n완료.")


if __name__ == "__main__":
    main()
