# -- coding: utf-8 --
# @Time : 2023/12/12 18:08
# @Author : zhuo.wang
# @File : main.py
from apscheduler.schedulers.background import BlockingScheduler
from strategy import strategy_factory
from order.enums import OrderKindEnum

if __name__ == '__main__':
    strategy = strategy_factory(name='m_head')
    scheduler = BlockingScheduler()
    model = strategy(symbol="ETHUSDT",
             interval='15m',
             backtest=False,
             usdt="ALL",
             leverage=10,
             order_kind=OrderKindEnum.BINANCE,
             )
    scheduler.add_job(model.execute, 'cron', hour='*',
                      minute='14,29,44,59', second='30',
                      )
    scheduler.start()
