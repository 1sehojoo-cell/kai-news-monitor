# KAI 데일리 브리핑 자동화

구글뉴스 + 방위사업청/국방부(보도자료·입찰공고) + 국내외 경쟁업체 동향을 매일 수집해
Claude API로 "정책-KAI 액션아이템 매핑 테이블" 형식 HTML 브리핑을 생성하고 이메일로 발송합니다.

## 1. 로컬 테스트

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
export SMTP_USER="you@gmail.com"
export SMTP_PASSWORD="구글앱비밀번호16자리"
export MAIL_TO="you@gmail.com"

python main.py
```

실행 후 `latest_briefing.html` 파일이 생성되며, 동시에 이메일이 발송됩니다.

## 2. Gmail 앱 비밀번호 발급

1. 구글 계정 > 보안 > 2단계 인증 활성화
2. 보안 > 앱 비밀번호 > "메일" 선택 후 생성된 16자리 비밀번호를 `SMTP_PASSWORD`로 사용
   (일반 로그인 비밀번호 아님)

## 3. GitHub Actions로 자동화

1. 이 폴더를 GitHub 저장소에 push
2. 저장소 Settings > Secrets and variables > Actions 에서 아래 3개 등록:
   - `ANTHROPIC_API_KEY`
   - `SMTP_USER`
   - `SMTP_PASSWORD`
   - `MAIL_TO` (여러 명이면 콤마로 구분: `a@x.com,b@y.com`)
3. `.github/workflows/daily-briefing.yml` 이 평일 KST 08:00에 자동 실행됨
   (Actions 탭에서 "Run workflow" 버튼으로 수동 실행도 가능)

## 4. 다음으로 해야 할 것 (중요)

`config.py` 안의 `GOV_SOURCES`, `COMPETITOR_SOURCES` 는 실제 사이트 HTML 구조를
직접 확인하지 않은 상태의 **추정 셀렉터**입니다. 배포 전 반드시:

1. 방위사업청 보도자료 게시판 / 국방전자조달(d2b.go.kr) 입찰공고 페이지의 실제 URL과
   테이블 구조(class명 등)를 확인해 `list_selector` / `title_selector` /
   `link_selector` / `date_selector` 를 맞게 수정
2. 한화에어로스페이스·LIG넥스원·현대로템 뉴스룸도 동일하게 확인
3. 록히드마틴은 RSS(`news.lockheedmartin.com/rss/...`)를 사용 중이므로 URL 유효성만 확인,
   보잉은 게시판 방식이라 셀렉터 확인 필요

실제 페이지를 하나씩 열어서 개발자도구(F12)로 구조를 보여주시면, 그 사이트에 맞는
정확한 셀렉터로 함께 수정해드릴 수 있습니다.

## 5. 파일 구성

| 파일 | 역할 |
|---|---|
| `config.py` | 소스 URL, 셀렉터, API/메일 설정 |
| `collectors.py` | RSS/게시판 스크래핑 |
| `summarizer.py` | Claude API 호출, HTML 요약 생성 |
| `mailer.py` | SMTP 이메일 발송 |
| `main.py` | 전체 파이프라인 실행 |
| `.github/workflows/daily-briefing.yml` | 평일 자동 실행 스케줄 |
