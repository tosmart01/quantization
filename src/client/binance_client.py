# -- coding: utf-8 --
# @Time : 2023/12/12 16:08
# @Author : pinbar
# @File : client.py

from binance.client import Client

from config.settings import BINANCE_KEY, BINANCE_SECRET, PROXIES

client = Client(BINANCE_KEY,
                BINANCE_SECRET,
                {
                    'proxies': PROXIES
                }
                )
