# -*- coding: utf-8 -*-
"""
summarizer가 생성한 JSON 데이터를 template.html(고정 틀)에 채워
최종 HTML 브리핑을 만듭니다.
"""

import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_briefing(data: dict) -> str:
    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("template.html")

    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    return template.render(
        report_date=today.strftime("%Y.%m.%d (%a)").replace(
            *_weekday_kr(today)
        ),
        report_datetime=today.strftime("%Y.%m.%d %H:%M"),
        period=f"{week_ago.strftime('%Y.%m.%d')} ~ {today.strftime('%Y.%m.%d')} (최근 1주일)",
        overseas=data["overseas"],
        gov_orgs=data["gov_orgs"],
        competitors=data["competitors"],
        narajangter=data["narajangter"],
        d2b=data["d2b"],
        agency_notices=data["agency_notices"],
        events=data["events"],
    )


def _weekday_kr(d: datetime.date):
    """strftime %a(영문 요일)를 한글로 치환하기 위한 (old, new) 튜플 반환."""
    kr = ["월", "화", "수", "목", "금", "토", "일"]
    eng = d.strftime("%a")
    return eng, kr[d.weekday()]
