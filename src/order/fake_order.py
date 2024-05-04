# -*- coding = utf-8 -*-
# @Time: 2024-04-05 15:28:42
# @Author: Donvink wuwukai
# @Site: 
# @File: fake_order.py
# @Software: PyCharm
from typing import TYPE_CHECKING
import pandas as pd

from order.enums import DirectionEnum

if TYPE_CHECKING:
    from schema.order_schema import OrderModel
    from schema.backtest import Backtest


class FakeOrder(object):
    @staticmethod
    def get_open_fake_order(symbol: str, backtest: "Backtest") -> "OrderModel":
        for order in backtest.order_list:
            if order.active and order.symbol == symbol:
                return order

    @staticmethod
    def create_fake_order(backtest: "Backtest", order_schema: "OrderModel") -> "OrderModel":
        backtest.order_list.append(order_schema)
        return order_schema

    @staticmethod
    def fake_stop_loss(order: "OrderModel", df: pd.DataFrame, direction: DirectionEnum,
                       backtest: "Backtest") -> bool:
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
            order.end_data = order.dict_to_order_field(current_k.to_dict())
            order.end_time = current_k.date
            order.close_price = close_price
            order.stop_loss = True
            return stop

    @staticmethod
    def close_fake_order(order: "OrderModel", df: pd.DataFrame):
        current_k: pd.Series = df.iloc[-1]
        order.active = False
        order.end_data = order.dict_to_order_field(current_k.to_dict())
        order.end_time = current_k.date
        order.close_price = current_k.close
