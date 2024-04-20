# -*- coding = utf-8 -*-
# @Time: 2024-04-05 15:28:42
# @Author: Donvink wuwukai
# @Site: 
# @File: fake_order.py
# @Software: PyCharm
import pandas as pd

from order.enums import DirectionEnum, SideEnum
from order.tools import get_stop_loss_price

from schema.backtest import Backtest
from schema.order_schema import OrderModel, OrderDataDict



class FakeOrder(object):
    def get_open_fake_order(self, symbol: str, backtest: Backtest) -> OrderModel:
        for order in backtest.order_list:
            if order.active and order.symbol == symbol:
                return order

    def create_fake_order(self, symbol: str, backtest: Backtest, df: pd.DataFrame, interval: str,
                          compare_k: pd.Series, side: SideEnum, leverage: int=None) -> OrderModel:
        k: pd.Series = df.iloc[-1]
        order_data = k.to_dict()
        order_data = OrderDataDict(**order_data)
        compare_data = OrderDataDict(**compare_k.to_dict())
        fake_order = OrderModel(symbol=symbol, active=True, start_time=k['date'], start_data=order_data,
                                open_price=k.close,
                                interval=interval, compare_data=compare_data, side=side, leverage=leverage)
        from strategy.tools import get_low_point
        stop_price = get_stop_loss_price(fake_order, k, df)
        fake_order.stop_price = stop_price
        low_point = get_low_point(df, fake_order)
        fake_order.low_point = low_point
        backtest.order_list.append(fake_order)
        return fake_order

    def fake_stop_loss(self, order: OrderModel, df: pd.DataFrame, direction: DirectionEnum, backtest: Backtest) -> bool:
        current_k: pd.Series = df.iloc[-1]
        stop = False
        close_price = None
        if direction == DirectionEnum.SHORT:
            if current_k.high >= order.stop_price:
                stop = True
                close_price = order.stop_price
        if direction == DirectionEnum.LONG:
            stop = current_k.low < order.compare_data.low
            close_price = order.compare_data.low
        if stop:
            order.active = False
            order.end_data = OrderDataDict(**current_k.to_dict())
            order.end_time = current_k.date
            order.close_price = close_price
            order.stop_loss = True
            return stop

    def close_fake_order(self, order: OrderModel, df: pd.DataFrame):
        current_k: pd.Series = df.iloc[-1]
        order.active = False
        order.end_data = OrderDataDict(**current_k.to_dict())
        order.end_time = current_k.date
        order.close_price = current_k.close
