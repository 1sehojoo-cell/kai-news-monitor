# -*- coding: utf-8 -*-
"""
소스별 수집기.
- collect_google_news(): 구글뉴스 RSS
- collect_gov_sources(): 방사청/국방부 등 정부 게시판
- collect_competitor_sources(): 국내외 경쟁사 뉴스룸
모든 수집 함수는 동일한 형태의 dict 리스트를 반환합니다:
  {"source": str, "title": str, "link": str, "date": str, "region": str}
"""

import time
import datetime
import xml.etree.ElementTree as ET
import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import quote

import config
import source_health


def _get(url: str) -> requests.Response | None:
    try:
        resp = requests.get(
            url, headers=config.REQUEST_HEADERS, timeout=config.REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"[WARN] 요청 실패: {url} ({e})")
        return None


def collect_google_news() -> list[dict]:
    """구글뉴스 RSS 검색 결과 수집 (기존 로직 유지)."""
    items = []
    for query in config.GOOGLE_NEWS_QUERIES:
        url = config.GOOGLE_NEWS_RSS_TEMPLATE.format(query=quote(query))
        feed = feedparser.parse(url)
        for entry in feed.entries[: config.MAX_ITEMS_PER_SOURCE]:
            items.append(
                {
                    "source": f"구글뉴스({query})",
                    "title": entry.get("title", "").strip(),
                    "link": entry.get("link", ""),
                    "date": entry.get("published", ""),
                    "region": "국내",
                }
            )
        time.sleep(0.5)
    return items


def _collect_rss(source_cfg: dict) -> list[dict]:
    feed = feedparser.parse(source_cfg["url"])
    items = []
    for entry in feed.entries[: config.MAX_ITEMS_PER_SOURCE]:
        items.append(
            {
                "source": source_cfg["name"],
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "date": entry.get("published", ""),
                "region": source_cfg.get("region", "-"),
            }
        )
    return items


def _collect_board(source_cfg: dict) -> list[dict]:
    """
    일반적인 HTML 게시판 리스트 스크래핑.
    사이트마다 구조가 달라 list_selector/title_selector/link_selector/date_selector를
    config.py에서 실제 구조에 맞게 조정해야 합니다.
    """
    resp = _get(source_cfg["url"])
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select(source_cfg["list_selector"])
    items = []

    for row in rows[: config.MAX_ITEMS_PER_SOURCE]:
        title_el = row.select_one(source_cfg["title_selector"])
        link_el = row.select_one(source_cfg["link_selector"])
        date_el = row.select_one(source_cfg.get("date_selector", ""))

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        link = link_el.get("href", "")
        # 상대경로 처리
        if link and not link.startswith("http"):
            base = "/".join(source_cfg["url"].split("/")[:3])
            link = base + ("" if link.startswith("/") else "/") + link.lstrip("/")

        date = date_el.get_text(strip=True) if date_el else ""

        items.append(
            {
                "source": source_cfg["name"],
                "title": title,
                "link": link,
                "date": date,
                "region": source_cfg.get("region", "-"),
            }
        )
    return items


def _collect_procurement_api(src: dict) -> list[dict]:
    """
    data.go.kr 기반 나라장터/국방전자조달 입찰공고 Open API 수집.
    API마다 JSON 또는 XML로 응답 형식이 달라, 둘 다 처리합니다.
    """
    if not config.DATA_GO_KR_SERVICE_KEY:
        print(f"[WARN] {src['name']}: DATA_GO_KR_SERVICE_KEY 미설정으로 건너뜀")
        return []
    try:
        today = datetime.datetime.now()
        week_ago = today - datetime.timedelta(days=7)
        begin_dt = week_ago.strftime("%Y%m%d0000")
        end_dt = today.strftime("%Y%m%d2359")

        query_string = (
            f"serviceKey={config.DATA_GO_KR_SERVICE_KEY}"
            f"&numOfRows={config.MAX_ITEMS_PER_SOURCE}&pageNo=1&type=json"
            f"&inqryDiv=1&inqryBgnDt={begin_dt}&inqryEndDt={end_dt}"
        )
        resp = requests.get(
            f"{src['url']}?{query_string}",
            headers=config.REQUEST_HEADERS,
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        print(f"[DEBUG] {src['name']} 응답 일부: {resp.text[:300]}")

        text = resp.text.strip()

        # XML로 응답하는 API 처리
        if text.startswith("<"):
            root = ET.fromstring(resp.text)
            items = []
            for item in root.findall(".//item"):
                title = (
                    item.findtext("bidNm")
                    or item.findtext("bidNtceNm")
                    or "제목 없음"
                )
                due = (
                    item.findtext("bidPartcptRegistClosDt")
                    or item.findtext("bidClseDt")
                    or ""
                )
                items.append(
                    {
                        "source": src["name"],
                        "title": title,
                        "link": "",
                        "date": due,
                        "region": "국내",
                    }
                )
            return items

        # JSON으로 응답하는 API 처리 (기존 로직)
        data = resp.json()
        body = data.get("response", {}).get("body", {})
        raw_items = body.get("items", [])
        if isinstance(raw_items, dict):
            raw_items = raw_items.get("item", [])
        if isinstance(raw_items, dict):
            raw_items = [raw_items]

        items = []
        for it in raw_items[: config.MAX_ITEMS_PER_SOURCE]:
            items.append(
                {
                    "source": src["name"],
                    "title": it.get("bidNtceNm", "제목 없음"),
                    "link": it.get("bidNtceDtlUrl", ""),
                    "date": it.get("bidClseDt") or it.get("bidNtceDt", ""),
                    "region": "국내",
                }
            )
        return items
    except Exception as e:
        print(f"[ERROR] {src['name']} API 수집 실패: {e}")
        return []


def collect_procurement_sources() -> list[dict]:
    """나라장터/D2B 공식 Open API로 입찰공고 수집."""
    items = []
    for src in config.PROCUREMENT_API_SOURCES:
        items.extend(_collect_procurement_api(src))
        time.sleep(0.3)
    return items


def collect_us_military_sources() -> list[dict]:
    """미군 각 군(육군/해군/공군/우주군) + 미 국방부 보도자료 수집. 매 실행 시 헬스체크 후 살아있는 소스만 수집."""
    print("[HEALTH] 미군 소스 점검 중...")
    alive = source_health.get_alive_sources(config.US_MILITARY_SOURCES)
    items = []
    for src in alive:
        try:
            items.extend(_collect_rss(src))
        except Exception as e:
            print(f"[ERROR] {src['name']} 수집 실패: {e}")
        time.sleep(0.5)
    return items


def collect_domestic_trade_sources() -> list[dict]:
    """국내 방산 전문매체(국방일보, 디펜스타임즈코리아 등) 수집. 매 실행 시 헬스체크 후 살아있는 소스만 수집."""
    print("[HEALTH] 국내 전문매체 점검 중...")
    alive = source_health.get_alive_sources(config.DOMESTIC_TRADE_SOURCES)
    items = []
    for src in alive:
        try:
            src = {**src, "region": "국내"}
            if src["type"] == "rss":
                items.extend(_collect_rss(src))
            else:
                items.extend(_collect_board(src))
        except Exception as e:
            print(f"[ERROR] {src['name']} 수집 실패: {e}")
        time.sleep(0.5)
    return items


def collect_overseas_trade_sources() -> list[dict]:
    """해외 방산 전문매체(Defense News, Breaking Defense 등) 수집. 매 실행 시 헬스체크 후 살아있는 소스만 수집."""
    print("[HEALTH] 해외 전문매체 점검 중...")
    alive = source_health.get_alive_sources(config.OVERSEAS_TRADE_SOURCES)
    items = []
    for src in alive:
        try:
            if src["type"] == "rss":
                items.extend(_collect_rss(src))
            else:
                items.extend(_collect_board(src))
        except Exception as e:
            print(f"[ERROR] {src['name']} 수집 실패: {e}")
        time.sleep(0.5)
    return items


def collect_gov_sources() -> list[dict]:
    """방위사업청 / 국방부 보도자료 + 입찰공고 수집. 매 실행 시 헬스체크 후 살아있는 소스만 수집."""
    print("[HEALTH] 정부기관 소스 점검 중...")
    alive = source_health.get_alive_sources(config.GOV_SOURCES)
    items = []
    for src in alive:
        try:
            if src["type"] == "rss":
                items.extend(_collect_rss(src))
            else:
                items.extend(_collect_board(src))
        except Exception as e:
            print(f"[ERROR] {src['name']} 수집 실패: {e}")
        time.sleep(0.5)
    return items


def collect_competitor_sources() -> list[dict]:
    """국내외 경쟁업체 뉴스룸 수집. 매 실행 시 헬스체크 후 살아있는 소스만 수집."""
    print("[HEALTH] 경쟁업체 소스 점검 중...")
    alive = source_health.get_alive_sources(config.COMPETITOR_SOURCES)
    items = []
    for src in alive:
        try:
            if src["type"] == "rss":
                items.extend(_collect_rss(src))
            else:
                items.extend(_collect_board(src))
        except Exception as e:
            print(f"[ERROR] {src['name']} 수집 실패: {e}")
        time.sleep(0.5)
    return items


def collect_all() -> dict[str, list[dict]]:
    """전체 소스를 카테고리별로 수집."""
    return {
        "google_news": collect_google_news(),
        "domestic_trade": collect_domestic_trade_sources(),
        "overseas_trade": collect_overseas_trade_sources(),
        "us_military": collect_us_military_sources(),
        "gov": collect_gov_sources(),
        "procurement": collect_procurement_sources(),
        "competitor": collect_competitor_sources(),
    }
