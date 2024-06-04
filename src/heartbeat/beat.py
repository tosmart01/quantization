# -- coding: utf-8 --
# @Time : 2024/6/4 10:02
# @Author : zhuo.wang
# @File : beat.py
from order.market import market
from notices.email_notify import send_mail, logger
from config.settings import RECEIVE_EMAIL


def heartbeat(strategy: str, symbol):
    try:
        market.get_open_order(symbol='BTCUSDT')
    except Exception:
        send_mail(mail_to=RECEIVE_EMAIL, subject=f'{symbol}-{strategy}心跳检测异常', content=f"{strategy}心跳检测异常")
    else:
        logger.info(f"{symbol}-{strategy}心跳检测 Success")