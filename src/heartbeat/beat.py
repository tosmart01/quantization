# -- coding: utf-8 --
# @Time : 2024/6/4 10:02
# @Author : zhuo.wang
# @File : beat.py
from client.binance_client import client
from notices.email_notify import send_mail
from config.settings import RECEIVE_EMAIL


def heartbeat(strategy: str):
    try:
        client.futures_klines(symbol='MATICUSDT', interval='15m', limit=10)
    except Exception:
        send_mail(mail_to=RECEIVE_EMAIL, subject=f'{strategy}心跳检测异常', content=f"{strategy}心跳检测异常")
    else:
        print(f"心跳检测 Success")