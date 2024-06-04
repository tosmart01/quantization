# -*- coding = utf-8 -*-
# @Time: 2024-06-01 15:19:12
# @Author: Donvink wuwukai
# @Site: 
# @File: nr4.py
# @Software: PyCharm
import numpy as np
import pandas as pd

from common.log import logger
from order.enums import SideEnum
from schema.order_schema import OrderModel, OrderDataDict
from strategy.base import BaseStrategy


class NrStrategy(BaseStrategy):
    limit = 20
    offset = 4

    def is_nr(self, data: list[dict]) -> bool:
        nr_list = data[-self.offset:]
        min_tr = np.min([i['tr'] for i in nr_list])
        max_tr = np.max([i['tr'] for i in nr_list])
        near = nr_list[-2]
        last = nr_list[-1]
        if min_tr == last['tr']:
            if last['high'] < near['high'] and last['low'] > near['low']:
                if last['high'] != last['close'] and last['low'] != last['close']:
                    if max_tr >= last['tr'] * 6:
                        return True
        return False

    def entry_signal(self, *args, **kwargs):
        df = self.data_module.get_klines(symbol=self.symbol, interval=self.interval,
                                                 backtest_info=self.backtest_info, limit=self.limit)
        current_k: pd.Series = df.iloc[-1]
        near_k: pd.Series = df.iloc[-2]
        list_dict: list[dict] = df.to_dict('records')
        is_nr = self.is_nr(list_dict[-self.offset - 1:-1])
        if not is_nr:
            return
        if current_k.high > near_k.high and current_k.low < near_k.low:
            return
        period: pd.DataFrame = df.iloc[-self.offset - 1: -1]
        tr_ratio = (period.tr.max() / near_k.tr)
        head_point = period.loc[period['high'].idxmax()]
        low_point = period.loc[period['low'].idxmin()]
        create = False
        if current_k.high > near_k.high:
            stop_price = near_k.low
            open_price = near_k.high * 1.0001
            side = SideEnum.BUY
            take_loss = (open_price - stop_price) / open_price
            create = True
        if current_k.low < near_k.low:
            stop_price = near_k.high
            side = SideEnum.SELL
            open_price = near_k.low * 0.9999
            take_loss = (stop_price - open_price) / open_price
            create = True
        if create and take_loss <= 0.02:
            order_schema = OrderModel(symbol=self.symbol,
                       active=True, start_time=current_k.date,
                       start_data=OrderDataDict(**current_k.to_dict()),
                       open_price=open_price,
                       stop_price=stop_price,
                       interval=self.interval,
                       side=side,
                       leverage=self.leverage,
                       low_point=OrderDataDict(**low_point.to_dict()),
                       head_point=OrderDataDict(**head_point.to_dict()),
                       tr_ratio=tr_ratio,
                       )
            logger.info(f"发现条件单={order_schema.symbol}, {current_k.date}")
            return self.order_module.create_order(self.backtest_info, df, order_schema=order_schema)


    def exit_signal(self, order: OrderModel):
        df = self.data_module.get_klines(symbol=self.symbol, interval=self.interval,
                                         backtest_info=self.backtest_info, limit=self.limit)
        stop_loss = self.order_module.check_stop_loss(order, df, order.side.direction(),
                                                      self.backtest_info)
        if stop_loss:
            return
        current_k = df.iloc[-1]
        k_count = (current_k.date - order.start_time).total_seconds() / 3600
        # is_nr = self.is_nr(df.tail(self.offset).to_dict('records'))
        # if is_nr and k_count >=2:
        #     return self.order_module.close_order(self.backtest_info, order, df)

        take_profit = (order.head_point.high - order.low_point.low) * 1
        current_profit = current_k.close - order.open_price if order.side == SideEnum.BUY else order.open_price - current_k.close
        if current_profit > take_profit:
            if order.side == SideEnum.BUY:
                if not (current_k.is_bull and df.iloc[-2].is_bull):
                    return self.order_module.close_order(self.backtest_info, order, df)
            else:
                if (current_k.is_bull and df.iloc[-2].is_bull):
                    return self.order_module.close_order(self.backtest_info, order, df)
        if k_count >= 8:
            return self.order_module.close_order(self.backtest_info, order, df)
