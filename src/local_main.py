# -- coding: utf-8 --
# @Time : 2024/5/7 17:53
# @Author : pinbar
# @File : local_main.py
from strategy import strategy_factory
from order.enums import OrderKindEnum

if __name__ == '__main__':
    model = strategy_factory('m_head')
    model(symbol='BTCUSDT',
          interval='1h',
          backtest=False,
          local_test=True,
          order_kind=OrderKindEnum.BINANCE).execute()
