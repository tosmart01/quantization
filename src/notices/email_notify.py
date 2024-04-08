# -*- coding = utf-8 -*-
# @Time: 2024-04-07 22:52:20
# @Author: Donvink wuwukai
# @Site: 
# @File: email_notify.py
# @Software: PyCharm

from service.email_service import send_mail
from common.log import logger


def send_trade_email(subject: str, content: str, to_recipients: list[str]):
    logger.info(f"开始发送邮件, {subject=}, {content=}, {to_recipients=}")
    try:
        send_mail(subject=subject, content=content, mail_to=to_recipients)
    except Exception:
        logger.exception(f"邮件发送失败, {subject=}, {content=}, {to_recipients=}")
    else:
        logger.info(f"邮件发送成功")

