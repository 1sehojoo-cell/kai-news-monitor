# -*- coding: utf-8 -*-
"""
뉴스 모니터링 시스템 설정 파일
소스 URL, 키워드, 메일 설정 등을 관리합니다.
"""

import os

# ============================================================
# 1. 구글 뉴스 (RSS 기반, 기존 유지)
# ============================================================
GOOGLE_NEWS_QUERIES = [
    "KAI 한국항공우주산업",
    "방위산업 국산 무기체계",
    "K-방산 수출",
    "국방 AI 국방혁신",
    "국방 무인기 드론",
    "국방 위성 우주"
    "유무인복합체계 MUM-T"
    "국방 전자전",
]
GOOGLE_NEWS_RSS_TEMPLATE = (
    "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
)

# ============================================================
# 2. 정부/연구기관 입찰·과제 소스
#    방사청(D2B), 나라장터(조달청)는 공식 Open API(data.go.kr)를 사용합니다.
#    - data.go.kr에서 "방위사업청_군수품조달정보 입찰공고", "나라장터 입찰공고정보서비스"
#      두 개를 신청하면 서비스키(ServiceKey)를 발급받을 수 있습니다.
#    국기연(PMS)·민진원·국과연(ADD)은 공지/보도자료 게시판을 스크래핑합니다.
# ============================================================
DATA_GO_KR_SERVICE_KEY = os.environ.get("DATA_GO_KR_SERVICE_KEY", "")

# data.go.kr Open API 기반 (type: "api")
PROCUREMENT_API_SOURCES = [
    {
        "name": "나라장터_입찰공고(용역)",
        "type": "api",
        "url": "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
    },
    {
        "name": "나라장터_입찰공고(물품)",
        "type": "api",
        "url": "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThng",
    },
    {
        "name": "국내 경쟁입찰공고 상세",
        "type": "api",
        "url": "https://apis.data.go.kr/1690000/BidPblancInfoService//getDmstcCmpetBidPblancDetail",
    },
]

# 게시판/공지사항 스크래핑 기반 (연구기관 과제공모)
GOV_SOURCES = [
    {
        "name": "방위사업청_보도자료",
        "type": "board",
        "url": "https://www.dapa.go.kr/dapa/na/ntt/selectNttList.do?bbsId=316",
        "list_selector": "table.board-list tbody tr",
        "title_selector": "td.title a",
        "link_selector": "td.title a",
        "date_selector": "td.date",
    },
    {
        "name": "국방기술진흥연구소(국기연)_공지사항",
        "type": "board",
        "url": "https://www.krit.re.kr/krit/bbs/notice_list.do?gotoMenuNo=05010000",
        "list_selector": "table.board-list tbody tr",
        "title_selector": "td.title a",
        "link_selector": "td.title a",
        "date_selector": "td.date",
    },
    {
        "name": "국기연_과제관리시스템(PMS) 공모",
        "type": "board",
        "url": "https://pms.krit.re.kr",  # 실제 공모 게시판 하위 경로는 접속 후 재확인 필요
        "list_selector": "table.board-list tbody tr",
        "title_selector": "td.title a",
        "link_selector": "td.title a",
        "date_selector": "td.date",
    },
    {
        "name": "민군협력진흥원(민진원)_공지사항",
        "type": "board",
        "url": "https://www.icmtc.re.kr",  # 실제 공지 게시판 하위 경로는 접속 후 재확인 필요
        "list_selector": "table.board-list tbody tr",
        "title_selector": "td.title a",
        "link_selector": "td.title a",
        "date_selector": "td.date",
    },
    {
        "name": "국방과학연구소(국과연/ADD)_공지사항",
        "type": "board",
        "url": "https://www.add.re.kr/kps",
        "list_selector": "table.board-list tbody tr",
        "title_selector": "td.title a",
        "link_selector": "td.title a",
        "date_selector": "td.date",
    },
]

# ============================================================
# 2-1. 국내 방산 전문매체
#    - 대부분 RSS를 제공하므로 RSS 우선, 없는 곳은 게시판 스크래핑
# ============================================================
DOMESTIC_TRADE_SOURCES = [
    {
        "name": "국방일보",
        "type": "rss",
        "url": "https://kookbang.dema.mil.kr/newsWeb/rss.do",
    },
    {
        "name": "디펜스타임즈코리아",
        "type": "rss",
        "url": "https://www.defensetimes.kr/rss/allArticle.xml",
    },
    {
        "name": "디펜스투데이",
        "type": "rss",
        "url": "https://www.defensetoday.co.kr/rss/allArticle.xml",
    },
    {
        "name": "월간 디펜스타임즈",
        "type": "rss",
        "url": "https://www.dtimes.co.kr/rss/allArticle.xml",
    },
    {
        "name": "무기박사(무기체계 전문)",
        "type": "rss",
        "url": "https://www.weaponsdaily.com/rss/allArticle.xml",
    },
    {
        "name": "연합뉴스_방위산업",
        "type": "rss",
        "url": "https://www.yna.co.kr/rss/defense.xml",
    },
    {
        "name": "뉴스1_방산",
        "type": "board",
        "url": "https://www.news1.kr/industry/defense",
        "list_selector": "div.list_wrap li",
        "title_selector": "a .tit",
        "link_selector": "a",
        "date_selector": "span.date",
    },
]

# ============================================================
# 2-2. 해외 방산 전문매체 (영문 → 요약 시 국문 처리)
# ============================================================
OVERSEAS_TRADE_SOURCES = [
    {
        "name": "Defense News",
        "type": "rss",
        "url": "https://www.defensenews.com/arc/outboundfeeds/rss/",
        "region": "해외",
    },
    {
        "name": "Breaking Defense",
        "type": "rss",
        "url": "https://breakingdefense.com/feed/",
        "region": "해외",
    },
    {
        "name": "Janes (제인스디펜스)",
        "type": "rss",
        "url": "https://www.janes.com/feeds/news",
        "region": "해외",
    },
    {
        "name": "Naval News",
        "type": "rss",
        "url": "https://www.navalnews.com/feed/",
        "region": "해외",
    },
    {
        "name": "The War Zone",
        "type": "rss",
        "url": "https://www.twz.com/feed",
        "region": "해외",
    },
    {
        "name": "C4ISRNET",
        "type": "rss",
        "url": "https://www.c4isrnet.com/arc/outboundfeeds/rss/",
        "region": "해외",
    },
    {
        "name": "SpaceNews",
        "type": "rss",
        "url": "https://spacenews.com/feed/",
        "region": "해외",
    },
    {
        "name": "Air & Space Forces Magazine",
        "type": "rss",
        "url": "https://www.airandspaceforces.com/feed/",
        "region": "해외",
    },
    {
        "name": "Shephard Media (무인체계 전문)",
        "type": "rss",
        "url": "https://www.shephardmedia.com/feed/",
        "region": "해외",
    },
    {
        "name": "SIPRI (스톡홀름국제평화연구소)",
        "type": "rss",
        "url": "https://www.sipri.org/rss.xml",
        "region": "해외",
    },
]

# ============================================================
# 3. 경쟁업체 (국내 4개사)
#    해외 경쟁사 동향은 별도 스크래핑 대신 위 OVERSEAS_TRADE_SOURCES(해외 전문매체) +
#    US_MILITARY_SOURCES(미군 각 군 보도자료)를 통해 커버합니다.
# ============================================================
COMPETITOR_SOURCES = [
    {
        "name": "한화에어로스페이스",
        "type": "board",
        "url": "https://www.hanwhaaerospace.co.kr/ko/newsroom/news/news-list.do",
        "list_selector": "ul.news-list li",
        "title_selector": "a .title",
        "link_selector": "a",
        "date_selector": "a .date",
        "region": "국내",
    },
    {
        "name": "대한항공_뉴스룸(항공우주사업)",
        "type": "board",
        "url": "https://news.koreanair.com/tag/%EB%AC%B4%EC%9D%B8%ED%95%AD%EA%B3%B5%EA%B8%B0/",
        "list_selector": "article.post, div.post-item",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "date_selector": "time, span.date",
        "region": "국내",
    },
    {
        "name": "LIG D&A(구 LIG넥스원)",
        "type": "board",
        "url": "https://www.lignex1.com/kr/pr/press.do",
        "list_selector": "table.board-list tbody tr",
        "title_selector": "td.title a",
        "link_selector": "td.title a",
        "date_selector": "td.date",
        "region": "국내",
    },
    {
        "name": "풍산_방산부문",
        "type": "board",
        "url": "https://www.poongsan.co.kr",  # 실제 보도자료 게시판 하위 경로는 접속 후 재확인 필요
        "list_selector": "table.board-list tbody tr",
        "title_selector": "td.title a",
        "link_selector": "td.title a",
        "date_selector": "td.date",
        "region": "국내",
    },
]

# ============================================================
# 3-1. 해외 경쟁사 동향 - 미군 각 군 보도자료 (해외 전문매체와 함께 ①해외 동향에 반영)
# ============================================================
US_MILITARY_SOURCES = [
    {
        "name": "US Army (defense.gov 연계)",
        "type": "rss",
        "url": "https://www.army.mil/rss/static/8.xml",
        "region": "해외",
    },
    {
        "name": "US Navy",
        "type": "rss",
        "url": "https://www.navy.mil/Press-Office/News-Stories/rss.aspx",
        "region": "해외",
    },
    {
        "name": "US Air Force",
        "type": "rss",
        "url": "https://www.af.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1",
        "region": "해외",
    },
    {
        "name": "US Space Force",
        "type": "rss",
        "url": "https://www.spaceforce.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=635",
        "region": "해외",
    },
    {
        "name": "DoD (미 국방부)",
        "type": "rss",
        "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945",
        "region": "해외",
    },
]

# ============================================================
# 4. Claude API 설정
# ============================================================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_SUMMARY_TOKENS = 4000

# ============================================================
# 5. 이메일 설정 (회사 Outlook/Exchange 기준)
#    - Gmail을 쓰실 경우 SMTP_HOST를 smtp.gmail.com 으로 바꾸면 됩니다.
# ============================================================
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")  # 회사 이메일 주소 (예: seho@kai.co.kr)
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")  # 계정 비밀번호 또는 앱 암호(MFA 사용 시)
MAIL_FROM = os.environ.get("MAIL_FROM", SMTP_USER)
MAIL_TO = os.environ.get("MAIL_TO", "")  # 콤마로 여러 명 가능: "a@x.com,b@y.com"
MAIL_SUBJECT_PREFIX = "[KAI 데일리 브리핑]"

# ============================================================
# 6. 스크래핑 공통 설정
# ============================================================
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
# 소스별 최대 수집 건수 (과금/노이즈 제어용)
MAX_ITEMS_PER_SOURCE = 8
