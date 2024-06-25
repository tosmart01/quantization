# -*- coding = utf-8 -*-
# @Time: 2024-06-23 14:52:08
# @Author: Donvink wuwukai
# @Site: 
# @File: three_day.py
# @Software: PyCharm
import pandas as pd

from common.tools import round_float_precision
from schema.order_schema import OrderModel, OrderDataDict
from .base import BaseStrategy
from order.enums import SideEnum


class ThreeDayStrategy(BaseStrategy):
    sell_setup = 9
    sell_step = 4
    buy_setup = 9
    buy_step = 4

    max_stop_ratio = 0.050

    def signal(self, df: pd.DataFrame) -> SideEnum:
        close_list = df.close.tolist()[::-1]
        count = 0
        for i in range(self.sell_setup):
            if close_list[i] < close_list[i + self.sell_step]:
                count += 1
        if count >= self.sell_setup:
            return SideEnum.SELL
        count = 0
        for i in range(self.buy_setup):
            if close_list[i] > close_list[i + self.buy_step]:
                count += 1
        if count >= self.buy_setup:
            return SideEnum.BUY


    def get_stop_price(self, df: pd.DataFrame, side: SideEnum):
        current_k = df.iloc[-1]
        # max_stop_ratio = min(df.close.pct_change().abs().mean() * 5, self.max_stop_ratio)
        max_stop_ratio = self.max_stop_ratio
        if side == SideEnum.SELL:
            return round_float_precision(current_k.close, current_k.close * (1 + max_stop_ratio))
        if side == SideEnum.BUY:
            return round_float_precision(current_k.close, current_k.close * (1 - max_stop_ratio))

    def exit_signal(self, order: OrderModel):
        df = self.data_module.get_futures_klines(self.symbol, self.interval, backtest_info=self.backtest_info)
        current_k = df.iloc[-1]
        stop_loss = self.order_module.check_stop_loss(order, df, order.side.direction(), self.backtest_info)
        k_count = (current_k.date - order.start_time).total_seconds() / 3600
        if stop_loss:
            return
        if order.side == SideEnum.BUY:
            # if current_k.close >= order.open_price: # + (order.open_price - order.stop_price) * 0.5 or k_count >= 30:
            if self.signal(df) == SideEnum.SELL:# or k_count >= 200:
                return self.order_module.close_order(self.backtest_info, order, df)
        if order.side == SideEnum.SELL:
            if self.signal(df) == SideEnum.BUY:# or k_count >= 200:
            # if current_k.close <= order.open_price: # - (order.stop_price - order.open_price) * 0.5 or k_count >= 30:
                return self.order_module.close_order(self.backtest_info, order, df)

    def entry_signal(self, *args, **kwargs):
        df = self.data_module.get_futures_klines(self.symbol, self.interval, backtest_info=self.backtest_info)
        current_k = df.iloc[-1]
        side = self.signal(df)
        if side is None:
            return
        stop_price = self.get_stop_price(df, side)
        order_schema = OrderModel(
            symbol=self.symbol,
            active=True,
            start_time=current_k.date,
            start_data=OrderDataDict(**current_k.to_dict()),
            open_price=current_k.close,
            interval=self.interval,
            side=side,
            leverage=self.leverage,
            stop_price=stop_price,
        )
        self.order_module.create_order(backtest=self.backtest_info, df=df, order_schema=order_schema,
                                       usdt=self.buy_usdt)
