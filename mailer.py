# -*- coding: utf-8 -*-
"""
SMTP를 통해 HTML 브리핑을 이메일로 발송합니다.
본문은 짧은 안내문, 전체 디자인은 HTML 파일로 첨부합니다.
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

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = config.MAIL_FROM
    msg["To"] = config.MAIL_TO

    # 본문: 짧은 안내문 (이메일 클라이언트에서 안 깨짐)
    plain_notice = (
        f"오늘의 산업동향 브리핑이 첨부파일로 도착했습니다.\n"
        f"첨부된 briefing_{today}.html 파일을 다운로드하여 열어보시면 "
        f"전체 디자인이 적용된 브리핑을 확인하실 수 있습니다."
    )
    msg.attach(MIMEText(plain_notice, "plain", "utf-8"))

    # 첨부파일: 원래 디자인이 그대로 살아있는 전체 HTML
    attachment = MIMEText(html_body, "html", "utf-8")
    attachment.add_header(
        "Content-Disposition", "attachment",
        filename=f"briefing_{today}.html"
    )
    msg.attach(attachment)

    recipients = [addr.strip() for addr in config.MAIL_TO.split(",") if addr.strip()]

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.MAIL_FROM, recipients, msg.as_string())

    print(f"[INFO] 이메일 발송 완료 (첨부파일 방식) -> {recipients}")
