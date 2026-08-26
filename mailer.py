# -*- coding: utf-8 -*-
"""
SMTP를 통해 HTML 브리핑을 이메일로 발송합니다.

회사 Outlook/Exchange 사용 시:
- SMTP_HOST=smtp.office365.com, SMTP_PORT=587 (기본값 이미 이렇게 설정됨)
- 회사가 MFA(다단계 인증)를 강제하는 경우, 일반 로그인 비밀번호로는 SMTP 인증이
  막힐 수 있어 Microsoft 계정의 "앱 암호(App Password)"를 발급받아 SMTP_PASSWORD에
  넣어야 합니다. 회사 IT 정책상 SMTP AUTH 자체가 차단된 경우 IT팀에 활성화 요청 필요.
- 사내 방화벽이 587 포트 아웃바운드를 막아둔 경우도 있어, 안 될 시 IT팀에 확인 필요.

Gmail 사용 시: 구글 계정 > 보안 > 2단계 인증 활성화 후 "앱 비밀번호" 발급 필요,
config.py의 SMTP_HOST를 smtp.gmail.com으로 변경.
"""

import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config


def send_html_email(html_body: str) -> None:
    if not (config.SMTP_USER and config.SMTP_PASSWORD and config.MAIL_TO):
        raise RuntimeError(
            "SMTP_USER / SMTP_PASSWORD / MAIL_TO 환경변수가 모두 설정되어야 합니다."
        )

    today = datetime.date.today().strftime("%Y-%m-%d")
    subject = f"{config.MAIL_SUBJECT_PREFIX} {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.MAIL_FROM
    msg["To"] = config.MAIL_TO

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    recipients = [addr.strip() for addr in config.MAIL_TO.split(",") if addr.strip()]

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.MAIL_FROM, recipients, msg.as_string())

    print(f"[INFO] 이메일 발송 완료 -> {recipients}")
