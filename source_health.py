# -*- coding: utf-8 -*-
"""
매 실행마다 config.py에 정의된 모든 RSS/게시판 소스가 실제로 살아있는지
자동으로 점검하고, 응답이 없거나 형식이 깨진 소스는 그날 수집 대상에서
자동으로 제외합니다. (URL이 사이트 개편으로 죽어도 파이프라인 전체가
멈추지 않도록 하기 위함)

동작 방식:
1. RSS 소스: HTTP 요청 후 feedparser로 파싱, entries가 1개 이상이면 정상
2. 게시판 소스: HTTP 요청 후 list_selector로 최소 1개 이상 행이 잡히면 정상
3. 결과를 콘솔에 요약 출력 + health_report.json 으로 저장 (이력 추적용)
"""

import json
import datetime
import feedparser
import requests
from bs4 import BeautifulSoup

import config

HEALTH_REPORT_PATH = "health_report.json"


def _check_rss(url: str) -> tuple[bool, str]:
    try:
        resp = requests.get(
            url, headers=config.REQUEST_HEADERS, timeout=config.REQUEST_TIMEOUT
        )
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        feed = feedparser.parse(resp.content)
        if len(feed.entries) == 0:
            return False, "RSS 파싱 성공했으나 entries 0건 (구조 변경 의심)"
        return True, f"OK ({len(feed.entries)}건 확인)"
    except requests.RequestException as e:
        return False, f"요청 실패: {e}"


def _check_board(src: dict) -> tuple[bool, str]:
    try:
        resp = requests.get(
            src["url"], headers=config.REQUEST_HEADERS, timeout=config.REQUEST_TIMEOUT
        )
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select(src["list_selector"])
        if len(rows) == 0:
            return False, "list_selector에 매칭되는 항목 0건 (셀렉터/구조 변경 의심)"
        return True, f"OK ({len(rows)}건 확인)"
    except requests.RequestException as e:
        return False, f"요청 실패: {e}"


def check_source(src: dict) -> dict:
    if src["type"] == "rss":
        ok, detail = _check_rss(src["url"])
    else:
        ok, detail = _check_board(src)
    return {"name": src["name"], "url": src["url"], "ok": ok, "detail": detail}


def check_all_sources() -> dict:
    """config.py에 등록된 모든 소스군을 점검하고 결과를 반환."""
    groups = {
        "domestic_trade": config.DOMESTIC_TRADE_SOURCES,
        "overseas_trade": config.OVERSEAS_TRADE_SOURCES,
        "us_military": config.US_MILITARY_SOURCES,
        "gov": config.GOV_SOURCES,
        "competitor": config.COMPETITOR_SOURCES,
    }

    results = {}
    for group_name, sources in groups.items():
        results[group_name] = [check_source(s) for s in sources]

    report = {
        "checked_at": datetime.datetime.now().isoformat(),
        "results": results,
    }

    with open(HEALTH_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def get_alive_sources(sources: list[dict]) -> list[dict]:
    """소스 리스트를 받아 살아있는 것만 필터링해서 반환 (수집 직전 호출용)."""
    alive = []
    for src in sources:
        result = check_source(src)
        status = "✅" if result["ok"] else "❌"
        print(f"  {status} {result['name']}: {result['detail']}")
        if result["ok"]:
            alive.append(src)
    return alive


def print_summary(report: dict) -> None:
    print(f"\n=== 소스 헬스체크 결과 ({report['checked_at']}) ===")
    total, alive = 0, 0
    for group_name, items in report["results"].items():
        group_alive = sum(1 for it in items if it["ok"])
        total += len(items)
        alive += group_alive
        print(f"[{group_name}] {group_alive}/{len(items)} 정상")
        for it in items:
            status = "✅" if it["ok"] else "❌"
            print(f"  {status} {it['name']} - {it['detail']}")
    print(f"\n총 {alive}/{total}개 소스 정상")


if __name__ == "__main__":
    report = check_all_sources()
    print_summary(report)
