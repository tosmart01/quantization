# -- coding: utf-8 --
# @Time : 2023/12/12 18:08
# @Author : zhuo.wang
# @File : main.py
from apscheduler.schedulers.background import BlockingScheduler

from config.settings import CRON_INTERVAL
from strategy import strategy_factory
from order.enums import OrderKindEnum

if __name__ == '__main__':
    strategy = strategy_factory(name='m_head')
    scheduler = BlockingScheduler()
    interval = '1h'
    model = strategy(symbol="ETHUSDT",
                     interval=interval,
                     backtest=False,
                     order_kind=OrderKindEnum.BINANCE,
                     )
    scheduler.add_job(model.execute, 'cron', hour='*',
                      minute=CRON_INTERVAL[interval], second='40',
                      )
    scheduler.start()
