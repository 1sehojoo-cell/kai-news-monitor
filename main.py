# -*- coding: utf-8 -*-
"""
메인 실행 스크립트.
1) 소스 수집 -> 2) Claude API 요약(HTML) -> 3) 이메일 발송
GitHub Actions에서 매일 평일 아침 실행됩니다.
"""

import sys
import datetime

import collectors
import summarizer
import renderer
import mailer


def main() -> int:
    print(f"[INFO] 브리핑 생성 시작: {datetime.datetime.now()}")

    # 1) 수집
    collected = collectors.collect_all()
    total = sum(len(v) for v in collected.values())
    print(
        f"[INFO] 수집 완료 - 구글뉴스:{len(collected['google_news'])}, "
        f"국내전문매체:{len(collected['domestic_trade'])}, "
        f"해외전문매체:{len(collected['overseas_trade'])}, "
        f"미군소스:{len(collected['us_military'])}, "
        f"정부/연구기관:{len(collected['gov'])}, 입찰공고API:{len(collected['procurement'])}, "
        f"경쟁사:{len(collected['competitor'])} "
        f"(총 {total}건)"
    )

    if total == 0:
        print("[WARN] 수집된 항목이 없어 브리핑을 생성하지 않습니다.")
        return 0

    # 2) 요약 (구조화 JSON)
    data = summarizer.summarize_to_data(collected)
    print(
        f"[INFO] 요약 완료 - 해외:{len(data['overseas'])}, 정부:{len(data['gov_orgs'])}, "
        f"경쟁사:{len(data['competitors'])}, 행사:{len(data['events'])}"
    )

    # 3) 고정 틀에 렌더링
    html = renderer.render_briefing(data)
    print(f"[INFO] 렌더링 완료 ({len(html)}자)")

    # 로컬 확인용 파일 저장 (GitHub Actions에서는 아티팩트로 남길 수 있음)
    with open("latest_briefing.html", "w", encoding="utf-8") as f:
        f.write(html)

    # 4) 발송
    mailer.send_html_email(html)

    print("[INFO] 전체 파이프라인 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
