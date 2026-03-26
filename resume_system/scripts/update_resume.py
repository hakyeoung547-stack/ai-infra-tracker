"""
update_resume.py

bullets/master_bullets.md의 내용을 읽어서
Claude API로 이력서 경험 섹션을 재구성하고
resume/master_resume.md를 업데이트한다.

사용법:
    python scripts/update_resume.py
"""

from pathlib import Path
import anthropic

ROOT = Path(__file__).parent.parent
MASTER_BULLETS = ROOT / "bullets" / "master_bullets.md"
MASTER_RESUME = ROOT / "resume" / "master_resume.md"

SYSTEM_PROMPT = """당신은 국내 기업 취업용 이력서 작성 전문가입니다.

주어진 bullet 목록을 바탕으로 이력서 "프로젝트 경험" 섹션을 작성하세요.

규칙:
1. 비슷한 bullet끼리 묶어서 3~5개의 대표 bullet으로 정리
2. 중복되거나 사소한 내용은 제거
3. 임팩트가 큰 것을 앞에 배치
4. 명사형 종결 (예: ~구축, ~개발, ~분석, ~자동화)
5. 각 bullet 앞에 사용 기술 태그 붙이기 (예: [Python] [Claude API])
6. 마크다운 형식으로 반환

출력 형식:
## 프로젝트명
*기간*

- [태그] bullet 내용
- [태그] bullet 내용
"""


def update_resume():
    bullets_content = MASTER_BULLETS.read_text()

    if not bullets_content.strip() or "자동 생성된 bullet" not in bullets_content and "###" not in bullets_content:
        print("bullet이 아직 없습니다. generate_bullets.py를 먼저 실행하세요.")
        return

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"아래 bullet 목록을 바탕으로 이력서 프로젝트 섹션을 작성해주세요.\n\n프로젝트명: AI 인프라 병목 분석 시스템\n기간: 2026.03 – 현재\n\n---\n{bullets_content}"
            }
        ]
    )

    resume_section = message.content[0].text

    # 기존 이력서 파일의 Experience 섹션 업데이트
    resume_content = MASTER_RESUME.read_text()

    # <!-- update_resume.py가 여기에 bullet을 자동 삽입함 --> 부분 교체
    marker = "<!-- update_resume.py가 여기에 bullet을 자동 삽입함 -->"
    if marker in resume_content:
        updated = resume_content.replace(marker, resume_section)
    else:
        # 마커 없으면 Experience 섹션 통째로 교체
        updated = resume_content + f"\n\n---\n\n{resume_section}"

    MASTER_RESUME.write_text(updated)
    print("resume/master_resume.md 업데이트 완료.")
    print("\n--- 생성된 섹션 미리보기 ---")
    print(resume_section[:500])
    if len(resume_section) > 500:
        print("... (이하 생략)")


if __name__ == "__main__":
    update_resume()
