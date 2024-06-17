# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:54:21
# @Author: Donvink wuwukai
# @Site: 
# @File: base.py
# @Software: PyCharm
import time
from abc import ABC, abstractmethod
from datetime import datetime

from common.log import logger
from common.tools import record_time
from config.settings import TRADE_MAX_INTERVAL, CRON_INTERVAL
from exceptions.custom_exceptions import DataDeficiencyError, DateTimeError, StrategyNotMatchError
from order import factory_order_model
from schema.backtest import Backtest
from order.enums import OrderKindEnum
from config.order_config import order_config
from schema.order_schema import OrderModel


class BaseStrategy(ABC):
    weekday_filter = []
    weekday_leverage_up = []
    weekday_leverage_down = []


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

    def filter_order(self, order_schema: OrderModel):
        weekday = order_schema.start_time.weekday() + 1
        if weekday in self.weekday_filter:
            logger.warning(f"星期过滤器生效,{weekday=}, 条件单symbol={self.symbol}")
            raise StrategyNotMatchError()
        if weekday in self.weekday_leverage_up:
            logger.warning(f"星期杠杆增强生效,{weekday=}，条件单symbol={self.symbol}")
            order_schema.leverage = order_schema.leverage + 2
        if weekday in self.weekday_leverage_down:
            logger.warning(f"星期杠杆降低生效,{weekday=}，条件单symbol={self.symbol}")
            order_schema.leverage = order_schema.leverage - 2

    @property
    def leverage(self):
        return order_config.leverage(symbol=self.symbol)

    @property
    def buy_usdt(self):
        if self.backtest_info.open_back:
            return 100
        all_money = self.order_module.get_all_money()
        _buy_usdt = order_config.buy_usdt(self.symbol)
        max_usdt = order_config.max_usdt(self.symbol)
        if _buy_usdt == 'ALL':
            return_u = round(all_money * 0.9, 2)
        elif "%" in str(_buy_usdt):
            usdt = float(_buy_usdt.split('%')[0]) / 100
            return_u = round(usdt * all_money, 2)
        else:
            if _buy_usdt > all_money:
                logger.warning(f"{self.symbol=} 下单金额超过账户余额，改为使用账户余额90%下单")
                return_u = round(all_money * 0.9, 2)
            else:
                return_u = _buy_usdt
        if max_usdt and return_u > max_usdt:
            return max_usdt
        return return_u

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

    @record_time
    def execute(self, *args, **kwargs):
        if not self.local_test:
            time_list = CRON_INTERVAL[self.interval]
            current_minute = datetime.now().minute
            if str(current_minute) not in time_list:
                raise DateTimeError()
            start_time = datetime.now().replace(second=57, microsecond=500 * 1000)
            while True:
                if (datetime.now() - start_time).total_seconds() < 0:
                    time.sleep(0.05)
                else:
                    break
        try:
            logger.info(f"symbol={self.symbol}开始执行,leverage={self.leverage}")
            order = self.order_module.get_open_order(self.symbol, self.backtest_info)
            if order:
                self.exit_signal(order)
            else:
                self.entry_signal()
        except Exception as e:
            logger.exception(f"执行异常")
            raise e

