# -*- coding = utf-8 -*-
# @Time: 2024-05-04 0:22:55
# @Author: Donvink wuwukai
# @Site: 
# @File: w_bottom.py
# @Software: PyCharm
import pandas as pd

from config.settings import NEAR_LOW_K_COUNT
from exceptions.custom_exceptions import StrategyNotMatchError
from src.strategy.base import BaseStrategy
from src.strategy.strategy_helper import find_low_index, recent_kline_avg_amplitude


class WBottomStrategy(BaseStrategy):

    def find_w_bottom_entry(self, df: pd.DataFrame):
        low_index_list = find_low_index(df, distance=12)
        if len(low_index_list) < 2:
            raise StrategyNotMatchError()
        current_k: pd.Series = df.iloc[-1]
        left_bottom: pd.Series = df.loc[low_index_list[-2]]
        right_bottom: pd.Series = df.loc[low_index_list[-1]]
        head_index = df.loc[left_bottom.name: right_bottom.name, 'high'].idxmax()
        head_point = df.loc[head_index]
        am = recent_kline_avg_amplitude(df.loc[left_bottom.name - 9: left_bottom.name])
        if current_k.close < left_bottom.low:
            raise StrategyNotMatchError()
        verify = (left_bottom.low - 0.65 * am) <= current_k.low <= (right_bottom.low + 0.85 * am)
        if verify and current_k.name - right_bottom.name <= NEAR_LOW_K_COUNT:
            if not current_k.is_bull:
                raise StrategyNotMatchError()
            expected_profit = (head_point.high - current_k.close) / current_k.close
            expected_loss = (current_k.close - right_bottom.low) / current_k.close
            profit_loss_ratio = expected_profit / expected_loss
            # 盈亏比判断
            if profit_loss_ratio >= 2.5:
                # 必须cover手续费
                if expected_profit >= 0.0015:
                    return

    def entry_signal(self):
        df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)

    def exit_signal(self, *args, **kwargs):
        ...

    def execute(self, *args, **kwargs):
        ...
