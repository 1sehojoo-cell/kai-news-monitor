# -*- coding: utf-8 -*-
"""
수집된 원문(dict 리스트)을 Claude API에 전달하여
고정 인포그래픽 템플릿(template.html)에 채울 구조화 JSON을 생성합니다.
자유 형식 HTML을 직접 생성하지 않고 JSON만 받는 이유:
틀(레이아웃/색상/구조)을 항상 동일하게 유지하기 위함입니다.
"""

import json
import datetime
import anthropic

import config

KST = datetime.timezone(datetime.timedelta(hours=9))

SYSTEM_PROMPT = """\
당신은 한국항공우주산업(KAI) 미래융합기술원의 방산동향 브리핑 작성자입니다.
아래 제공되는 원문 목록(해외 방산 뉴스, 방위사업청/국방부 보도자료 및 입찰공고,
국내외 경쟁업체 뉴스)을 바탕으로, 고정된 인포그래픽 틀에 채워 넣을 데이터를
JSON으로만 출력하세요. 설명, 마크다운 코드펜스(```) 등 JSON 이외의 텍스트는 절대 출력하지 마세요.

다음 스키마를 정확히 따르세요 (키 이름 그대로 사용):

{
  "overseas": [                      // ① 해외 방산 동향 - 최대 4건, 중요도 높은 순
    {"icon": "이모지 1개(주제에 맞게, 예: ✈️ 🚀 🛰️)", "title": "제목(간결하게)",
     "source": "언론사명 (원문일자)", "bullets": ["핵심내용1", "핵심내용2"]}
  ],
  "gov_orgs": [                      // ② 군/유관기관 주요 동향 - 최대 5건
                                      // (정부/군 기관 자체가 주체인 정책·인사·훈련·예산 소식만.
                                      //  기업이 주체인 계약/수출/제품 소식은 여기 넣지 말고 competitors로)
    {"org": "기관명(예: 국방부, 해군본부, 방위사업청)", "title": "제목(날짜 포함 가능)",
     "bullets": ["핵심내용1", "핵심내용2"], "source": "출처"}
     
  ],
  "competitors": [                   // ③ 경쟁업체 주요 동향 - 각 경쟁사 최대 3건
                                      // (기업이 주체인 소식. 정부기관과의 계약이어도 기업이 주어라면 여기로)
    {"icon": "이모지 1개", "company": "회사명", "summary": "요약(2문장 이내)",
     "source_title": "언론사/매체명 기사제목 축약", "date": "YYYY-MM-DD"}
  ],
  "narajangter": [                   // 나라장터(조달청) 공고 - 없으면 빈 배열
    {"title": "사업/과제명", "due": "YYYY-MM-DD", "org": "공고기관"}
  ],
  "d2b": [                           // 국방전자조달시스템(국방부) 공고 - 없으면 빈 배열
    {"title": "사업/과제명", "due": "YYYY-MM-DD", "org": "공고기관"}
  ],
  "agency_notices": [                // 기타 주요 기관 공고
    {"org": "기관명", "title": "사업/과제명", "due": "YYYY-MM-DD", "source": "출처(도메인 등)"}
  ],
  "events": [                        // ④ 향후 1주일 공식 행사 일정 - 원문에 명시된 것만
    {"date": "YYYY-MM-DD(요일) 형식", "org_name": "기관/행사명",
     "content": "주요내용(bullet 여러개면 · 로 구분)", "location": "장소"}
  ]
}

규칙:
0. 아래 4개 핵심 테마와 관련된 내용만 선별하세요: ① 위성/우주 ② 무인기·드론 ③ AI·전자전 ④ 유·무인복합체계(MUM-T).
   이 테마와 무관한 내용(단순 인사발령, 일반 재무실적 발표, 테마와 무관한 사업 등)은
   overseas, gov_orgs, competitors뿐 아니라 narajangter, d2b, agency_notices에서도
   모두 제외하세요. 즉 입찰공고/과제공고도 위 4개 테마와 관련 있는 것만 포함합니다.
1. 원문에 없는 사실은 절대 지어내지 마세요. 행사 일정(events)이나 공고 정보가 원문에 없으면 빈 배열([])로 두세요.
2. "KAI 관점 시사점"처럼 분석적 해석이 필요한 항목은 bullets 안에 마지막 줄로 "→ KAI 시사점: ..." 형태로 포함하세요.
3. 항목이 많으면 테마 관련성 및 중요도(방산/정책 영향력) 기준으로 선별하고, 각 배열의 최대 건수를 넘기지 마세요.
4. source_title, source 등에는 실제 원문의 출처명을 사용하세요.
5. 반드시 유효한 JSON만 출력하세요.
6. 동일한 사건/기사를 여러 카테고리에 중복으로 넣지 마세요. 기사의 핵심 주어가 "정부/군 기관"이면
   gov_orgs에만, 핵심 주어가 "기업"이면 competitors에만 넣으세요. 예: "방위사업청이 A사와 계약 체결"
   기사는 계약의 주체가 기업 활동(수주)이므로 competitors에만 넣고, gov_orgs에는 넣지 마세요.
"""


def _format_items_for_prompt(items: list[dict], label: str) -> str:
    if not items:
        return f"### {label}\n(수집된 항목 없음)\n"
    lines = [f"### {label}"]
    for it in items:
        lines.append(
            f"- 출처: {it['source']} | 제목: {it['title']} | "
            f"날짜: {it.get('date', '-')} | 링크: {it.get('link', '-')}"
        )
    return "\n".join(lines)


def build_prompt(collected: dict[str, list[dict]]) -> str:
    today = datetime.datetime.now(KST).strftime("%Y년 %m월 %d일")
    parts = [f"오늘 날짜: {today}\n"]
    parts.append(_format_items_for_prompt(collected.get("gov", []), "정부/연구기관 공지 소스 (국기연·민진원·국과연·방사청)"))
    parts.append(
        _format_items_for_prompt(
            collected.get("procurement", []), "나라장터/D2B 실시간 입찰공고 (Open API, ⑤신규 사업/과제 공고에 직접 매핑)"
        )
    )
    parts.append(
        _format_items_for_prompt(collected.get("competitor", []), "국내 경쟁업체 소스 (한화에어로스페이스/대한항공/LIG D&A/풍산)")
    )
    parts.append(
        _format_items_for_prompt(
            collected.get("overseas_trade", []), "해외 방산 전문매체 소스 (①해외 방산 동향에 우선 반영)"
        )
    )
    parts.append(
        _format_items_for_prompt(
            collected.get("us_military", []), "미군 각 군/국방부 보도자료 (①해외 방산 동향 - 해외 경쟁사 동향 참고)"
        )
    )
    parts.append(
        _format_items_for_prompt(
            collected.get("domestic_trade", []), "국내 방산 전문매체 소스 (②/기타 동향에 반영)"
        )
    )
    parts.append(
        _format_items_for_prompt(collected.get("google_news", []), "구글뉴스 일반 검색 소스")
    )
    return "\n\n".join(parts)


def summarize_to_data(collected: dict[str, list[dict]]) -> dict:
    """수집 데이터를 Claude API로 요약하여 템플릿용 JSON(dict) 반환."""
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    user_prompt = build_prompt(collected)

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.MAX_SUMMARY_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Claude 응답이 JSON 형식이 아닙니다: {e}\n원문: {raw[:500]}")

    for key in [
        "overseas", "gov_orgs", "competitors",
        "narajangter", "d2b", "agency_notices", "events",
    ]:
        data.setdefault(key, [])

    return data
