# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:54:21
# @Author: Donvink wuwukai
# @Site: 
# @File: base.py
# @Software: PyCharm
from abc import ABC, abstractmethod

from common.log import logger
from config.settings import TRADE_MAX_INTERVAL
from exceptions.custom_exceptions import DataDeficiencyError
from order import factory_order_model
from schema.backtest import Backtest
from order.enums import OrderKindEnum
from config.order_config import order_config


class BaseStrategy(ABC):

    def __init__(self, symbol: str, interval: str = '15m', backtest: bool = False,
                 back_start_date: str = None, back_end_date: str = None, order_kind: OrderKindEnum = None,
                 backtest_path: str = "", local_test: bool = False, backtest_future_path: str = None):
        from dataset.dataset_tools import DataModule
        self.data_module = DataModule()
        self.symbol = symbol
        self.interval = interval
        self.order_module = factory_order_model(order_kind)
        self.backtest_info = self.backtest_init(backtest, back_start_date, back_end_date, backtest_path, backtest_future_path)
        self.local_test = local_test

    @property
    def leverage(self):
        return order_config.leverage(symbol=self.symbol)

    @property
    def buy_usdt(self):
        if self.backtest_info.open_back:
            return 100
        all_money = self.order_module.get_all_money()
        _buy_usdt = order_config.buy_usdt(self.symbol)
        if _buy_usdt == 'ALL':
            return round(all_money * 0.9, 2)
        elif "%" in str(_buy_usdt):
            usdt = float(_buy_usdt.split('%')[0]) / 100
            return round(usdt * all_money, 2)
        else:
            if _buy_usdt > all_money:
                logger.warning(f"{self.symbol=} 下单金额超过账户余额，改为使用账户余额90%下单")
                return round(all_money * 0.9, 2)
            else:
                return _buy_usdt

    def backtest_init(self, backtest, back_start_date, back_end_date, backtest_path: str, backtest_future_path: str) -> Backtest:
        if backtest:
            test_df = self.data_module.load_fake_klines(backtest_path)
            future_test_df = self.data_module.load_fake_klines(backtest_future_path)
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
                            end_offset=end_offset,
                            future_df=future_test_df,
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
