# -*- coding = utf-8 -*-
# @Time: 2024-04-07 22:55:34
# @Author: Donvink wuwukai
# @Site: 
# @File: decorator.py
# @Software: PyCharm
from traceback import format_exc
from common.log import logger
from config.settings import RECEIVE_EMAIL
from notices.email_notify import send_trade_email
from config.settings import MODEL_TEST


def error_email_notify(name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not MODEL_TEST:
                    logger.warning(f"{name}执行异常，发送提醒邮件")
                    message = "详细信息" + "<br><br><pre>" + format_exc().replace("\n", "<br>").replace(" ",
                                                                                                        "&nbsp;") + "</pre>"
                    send_trade_email(subject=f"【{name}执行异常】", content=message, to_recipients=RECEIVE_EMAIL)
                raise e

        return wrapper

    return decorator
