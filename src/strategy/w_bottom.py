# -*- coding = utf-8 -*-
# @Time: 2024-05-04 0:22:55
# @Author: Donvink wuwukai
# @Site: 
# @File: w_bottom.py
# @Software: PyCharm
import time
from datetime import datetime

import pandas as pd

from common.log import logger
from common.tools import record_time
from config.settings import NEAR_LOW_K_COUNT, CRON_INTERVAL
from exceptions.custom_exceptions import StrategyNotMatchError, DateTimeError
from order.enums import SideEnum, DirectionEnum
from schema.order_schema import OrderModel, OrderDataDict
from src.strategy.base import BaseStrategy
from src.strategy.strategy_helper import find_low_index, recent_kline_avg_amplitude, find_high_index


class WBottomStrategy(BaseStrategy):
    distance = 15
    prominence = 5
    compare_low_k_count = 2
    w_decline_percent = 3
    loss_decrease_percent = 0.4
    max_stop_loss = 0.03

    def get_stop_price(self, df: pd.DataFrame, right_bottom: pd.Series, current_k: pd.Series) -> float:
        stop_pct_change = (df.tr.mean() / df.close.mean()) * self.w_decline_percent * self.loss_decrease_percent
        right_bottom_loss = (current_k.close - right_bottom.low) / current_k.close
        stop_price = right_bottom.low
        if (current_k.close - current_k.low) / current_k.close >= stop_pct_change:
            stop_price = current_k.low
        max_stop_value = current_k.close * (1 - self.max_stop_loss)
        return max(max_stop_value, stop_price)

    def get_head_point(self, df: pd.DataFrame, left_bottom: pd.Series, right_bottom: pd.Series) -> pd.Series:
        high_index_list = find_high_index(df, distance=self.distance, prominence=self.prominence)
        head_index = df.loc[left_bottom.name + 1: right_bottom.name - 1, 'high'].idxmax()
        head_point = df.loc[head_index]
        min_pct_change = (df.tr.mean() / df.close.mean()) * self.w_decline_percent
        head_pct = (head_point.high - right_bottom.low) / head_point.high
        left_head = None
        for index in high_index_list:
            if index < left_bottom.name:
                left_head = df.loc[index]
                break
        if head_pct >= min_pct_change:
            return head_point
        if left_head is not None:
            left_pct = (left_head.high - left_bottom.low) / left_head.high
            if left_pct >= min_pct_change:
                return head_point
            print(f"涨幅过滤,{min_pct_change=:.4f}, {head_pct=:.4f}, {left_pct=:.4f}")
        raise StrategyNotMatchError()

    def check_point_range(self, df: pd.DataFrame, left_bottom: pd.Series, right_bottom: pd.Series):
        am = (recent_kline_avg_amplitude(df.loc[right_bottom.name - 9: right_bottom.name]) + \
              recent_kline_avg_amplitude(df.loc[left_bottom.name - 9: left_bottom.name])) / 2
        verify_list = [am * 0.55 <= abs(right_bottom.low - left_bottom.low) <= am * 1.6,
                       abs(right_bottom.low - left_bottom.low) <= am * 0.15
                       ]
        return any(verify_list)

    def check_w_bottom(self, df: pd.DataFrame, left_bottom: pd.Series, right_bottom: pd.Series):
        current_k = df.iloc[-1]
        # bottom_pct = (right_bottom.low - left_bottom.low) / right_bottom.low
        stop_price = self.get_stop_price(df, right_bottom, current_k)
        if current_k.close < right_bottom.low or current_k.close < stop_price:
            raise StrategyNotMatchError()
        verify = self.check_point_range(df, left_bottom, right_bottom)
        if verify and current_k.name - right_bottom.name <= NEAR_LOW_K_COUNT:
            head_point = self.get_head_point(df, left_bottom, right_bottom)
            expected_profit = (head_point.high - current_k.close) / current_k.close
            expected_loss = (current_k.close - right_bottom.low) / current_k.close
            profit_loss_ratio = expected_profit / expected_loss
            # 必须cover手续费
            return OrderModel(symbol=self.symbol,
                              active=True, start_time=current_k.date,
                              start_data=OrderDataDict(**current_k.to_dict()),
                              open_price=current_k.close,
                              interval=self.interval,
                              side=SideEnum.BUY,
                              leverage=self.leverage,
                              stop_price=stop_price,
                              left_bottom=OrderDataDict(**left_bottom),
                              right_bottom=OrderDataDict(**right_bottom),
                              head_point=OrderDataDict(**head_point),
                              )
            # print(f"盈亏比判断------------------------------")

    def find_w_bottom_entry(self, df: pd.DataFrame) -> OrderModel:
        low_index_list = find_low_index(df, distance=self.distance, prominence=self.prominence)
        if len(low_index_list) < 2:
            raise StrategyNotMatchError()
        current_k: pd.Series = df.iloc[-1]
        if not current_k.is_bull:
            raise StrategyNotMatchError()
        right_bottom: pd.Series = df.loc[low_index_list[-1]]
        compare_low_list = [-i - 2 for i in range(len(low_index_list) - 1)][:self.compare_low_k_count]
        before_left_bottom = None
        for index in compare_low_list:
            left_bottom: pd.Series = df.loc[low_index_list[index]]
            if before_left_bottom is not None and left_bottom.low > before_left_bottom.low:
                break
            try:
                order = self.check_w_bottom(df, left_bottom, right_bottom)
                if order is not None:
                    return order
            except StrategyNotMatchError:
                pass
            before_left_bottom = left_bottom

    def entry_signal(self):
        df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        try:
            order_schema = self.find_w_bottom_entry(df)
        except StrategyNotMatchError:
            order_schema = None
        if order_schema:
            logger.info(f"条件单出现, symbol={self.symbol}, 日期={df.iloc[-1]['date']}")
            order = self.order_module.create_order(backtest=self.backtest_info,
                                                   df=df,
                                                   usdt=self.buy_usdt,
                                                   order_schema=order_schema
                                                   )
            return order

    def exit_signal(self, order: OrderModel):
        df = self.data_module.get_klines(order.symbol, interval=order.interval, backtest_info=self.backtest_info)
        stop_loss = self.order_module.check_stop_loss(order, df, DirectionEnum.LONG, self.backtest_info)
        if stop_loss:
            return
        high_value = order.head_point.high
        current_k = df.iloc[-1]
        start_k = df.loc[df.date == order.start_data.date].iloc[0]
        min_trade_day = 10
        trade_day = current_k.name - start_k.name
        am = recent_kline_avg_amplitude(df.loc[current_k.name - 30: current_k.name])
        verify = False
        for k in df.loc[current_k.name - 2: current_k.name].itertuples():
            verify = (high_value - 0.1 * am) <= k.high <= (high_value + 0.1 * am) and not current_k.is_bull
            if verify:
                break
            if current_k.close > high_value and not current_k.is_bull:
                verify = True
                break
        loss_k_count = df.loc[current_k.name - 2: current_k.name, 'is_bull'].sum()
        if verify and trade_day >= min_trade_day:
            self.order_module.close_order(self.backtest_info, order, df)
        elif loss_k_count == 0 and trade_day >= min_trade_day:
            self.order_module.close_order(self.backtest_info, order, df)
        elif trade_day >= 80:
            self.order_module.close_order(self.backtest_info, order, df)

    @record_time
    def execute(self, *args, **kwargs):
        time_list = CRON_INTERVAL[self.interval]
        current_minute = datetime.now().minute
        if str(current_minute) not in time_list:
            raise DateTimeError()
        while True:
            period = 60 - datetime.now().second
            if period >= 3:
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
