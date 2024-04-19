# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:54:21
# @Author: Donvink wuwukai
# @Site: 
# @File: base.py
# @Software: PyCharm
from abc import ABC, abstractmethod

import pandas as pd

from config.settings import MAX_VALUE_PERIOD, DECLINE_HIGH_TIME, TRADE_MAX_INTERVAL
from exceptions.custom_exceptions import DataDeficiencyError
from order import factory_order_model
from schema.backtest import Backtest
from order.enums import OrderKindEnum


class BaseStrategy(ABC):

    def __init__(self, symbol: str, interval: str = '15m', backtest: bool = False,
                 back_start_date: str = None,
                 back_end_date: str = None, leverage: int = 5, order_kind: OrderKindEnum = None,
                 usdt: float | str = None):
        from dataset.dataset_tools import DataModule
        self.data_module = DataModule()
        self.symbol = symbol
        self.interval = interval
        self.order_module = factory_order_model(order_kind)
        self.backtest_info = self.backtest_init(backtest, back_start_date, back_end_date)
        self.leverage = leverage
        self.usdt = usdt

    @property
    def buy_usdt(self):
        if self.backtest_info.open_back:
            return 100
        if self.usdt == 'ALL':
            return round(self.order_module.get_all_money() * 0.85, 2)
        else:
            return self.usdt

    def backtest_init(self, backtest, back_start_date, back_end_date) -> Backtest:
        if backtest:
            test_df = self.data_module.load_fake_klines(self.symbol)
            if back_start_date and back_end_date:
                test_df = test_df.loc[(test_df['date'] >= back_start_date) & (test_df['date'] <= back_end_date)]
            if test_df.empty:
                raise DataDeficiencyError()
            start_offset = 0
            end_offset = TRADE_MAX_INTERVAL - 1
            return Backtest(symbol=self.symbol,
                            df=test_df,
                            open_back=True,
                            start_offset=start_offset,
                            end_offset=end_offset
                            )
        return Backtest(symbol=self.symbol)

    @abstractmethod
    def entry_signal(self, *args, **kwargs):
        ...

    @abstractmethod
    def exit_signal(self, *args, **kwargs):
        ...

    @abstractmethod
    def execute(self, *args, **kwargs):
        ...
