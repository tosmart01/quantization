# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:24:26
# @Author: Donvink wuwukai
# @Site: 
# @File: m_head.py
# @Software: PyCharm
import time
from datetime import datetime, timedelta
import pandas as pd

from common.log import logger
from common.tools import record_time
from config.settings import M_DECLINE_PERCENT, CRON_INTERVAL
from strategy.base import BaseStrategy
from strategy.tools import recent_kline_avg_amplitude, find_high_index, get_shadow_line_ratio, find_low_index, \
    check_high_value_in_range
from order.enums import DirectionEnum, SideEnum
from schema.order_schema import OrderModel
from exceptions.custom_exceptions import DateTimeError


class MHeadStrategy(BaseStrategy):

    def check_near_volume(self, current_k: pd.Series, compare_k: pd.Series, df: pd.DataFrame) -> bool:
        current_volume = df.loc[current_k.name - 1: current_k.name + 1, 'volume'].mean()
        compare_volume = df.loc[compare_k.name - 1: compare_k.name + 1, 'volume'].mean()
        return current_volume <= compare_volume

    def find_enter_point(self, compare_high_index: int, df: pd.DataFrame, high_index_list: list) -> tuple[
        bool, pd.Series]:
        compare_high_k = df.loc[high_index_list[compare_high_index]]
        last_high_k = df.loc[high_index_list[-1]]
        last_k: pd.Series = df.iloc[-1]
        if last_k.close >= compare_high_k.high:
            return False, last_k
        AM = recent_kline_avg_amplitude(df.loc[compare_high_k.name - 9: compare_high_k.name])
        low_value = df.loc[compare_high_k.name: last_k.name, 'low'].min()
        pct_change_verify = [(last_k.high - low_value) / low_value > M_DECLINE_PERCENT,
                             (last_high_k.high - low_value) / low_value > M_DECLINE_PERCENT
                             ]
        ge_last_high_k_list = []
        near_high_list = []
        is_near_high_k = last_k.name - last_high_k.name <= 4
        if self.high_interval_check(last_k, last_high_k) and any(pct_change_verify):
            overtop = False
            compare_range = last_high_k.name - 3 if is_near_high_k else last_k.name - 4
            mid = df.loc[last_high_k.name - 4: last_high_k.name, 'close'].mean()
            for k in df.loc[compare_range: last_k.name].itertuples():
                current_am = recent_kline_avg_amplitude(df.loc[k.Index - 9: k.Index])
                # 命中价格区间
                verify = check_high_value_in_range(k, compare_high_k, AM)
                shadow_ratio = get_shadow_line_ratio(k)
                # 上引线过长排除
                if shadow_ratio >= 0.5 and current_am * 1.5 < k.high - k.low:
                    verify = False
                if k.high < mid:
                    verify = False
                # 涨幅过大排除
                if k.high > (compare_high_k.high + 1 * AM) and is_near_high_k:
                    overtop = True
                if verify and k.high > compare_high_k.high:
                    ge_last_high_k_list.append(True)
                near_high_list.append(verify)
            verify_length = len(list(filter(None, near_high_list)))
            if verify_length >= 1 and not overtop and len(ge_last_high_k_list) <= 2:
                # 阴线命中
                if last_k.close < last_k.open:
                    # 命中k线涨幅限制
                    if abs(last_k.close - last_k.open) <= 1.5 * AM:
                        # if self.check_near_volume(last_high_k, compare_high_k, df):
                        return (True, compare_high_k)
        return False, compare_high_k

    def check_near_prior_high_point(self, df: pd.DataFrame) -> tuple[bool, pd.Series]:
        high_index_list = find_high_index(df, prominence=0)
        if len(high_index_list) < 2:
            return False, df.iloc[1]
        compare_high_list = [-i - 2 for i in range(len(high_index_list) - 1)][:3]
        for index in compare_high_list:
            verify, compare_high_k = self.find_enter_point(index, df, high_index_list)
            if verify:
                return verify, compare_high_k
        return False, df.loc[0]

    def get_low_point(self, df: pd.DataFrame, order: OrderModel) -> pd.Series | None:
        low_index_list = find_low_index(df)
        low_df = df.loc[low_index_list]
        low_point_left = low_df.loc[low_df['date'] < order.compare_data.date]
        low_point_right = low_df.loc[low_df['date'] > order.compare_data.date]
        low_point = None
        if not low_point_right.empty:
            low_point = low_point_right.iloc[0]
        elif not low_point_left.empty:
            low_point = low_point_left.iloc[-1]
        start_k = df.loc[df['date'] == order.start_data.date].iloc[-1]
        if abs(start_k.name - low_point.name) <= 8:
            return None
        return low_point

    def entry_signal(self) -> OrderModel:
        df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        verify, compare_k = self.check_near_prior_high_point(df)
        if verify:
            logger.info(f"条件单出现, symbol={self.symbol}, 日期={df.iloc[-1]['date']}")
            order = self.order_module.create_order(symbol=self.symbol,
                                                   backtest=self.backtest_info,
                                                   df=df,
                                                   interval=self.interval,
                                                   compare_k=compare_k,
                                                   side=SideEnum.SELL,
                                                   leverage=self.leverage,
                                                   usdt=self.buy_usdt
                                                   )
            return order

    def exit_signal(self, order: OrderModel):
        df = self.data_module.get_klines(order.symbol, interval=order.interval, backtest_info=self.backtest_info)
        stop_loss = self.order_module.check_stop_loss(order, df, DirectionEnum.SHORT, self.backtest_info)
        if stop_loss:
            return
        checkout = False
        current_k: pd.Series = df.iloc[-1]
        min_k_count = 8
        start_k = df.loc[df['date'] == order.start_data.date].iloc[0]
        AM = recent_kline_avg_amplitude(df.loc[current_k.name - 9: current_k.name])
        low_point = self.get_low_point(df, order)
        if low_point is not None:
            # 近3跟k线接近前期低点，并且当前k线收阳线，平仓
            for row in df.loc[current_k.name - 2: current_k.name].itertuples():
                if abs(row.low - low_point.close) <= AM * 0.10 and current_k.is_bull:
                    checkout = True
                    break
                # 如果已经低于前期低点，收阳线平仓
                if row.low < low_point.close and current_k.is_bull:
                    checkout = True
                    break
        if not checkout:
            count = 0
            for row in df.loc[current_k.name - 2: current_k.name].itertuples():
                if row.close - row.open > 0:
                    count += 1
            if count >= 3 and current_k.name - start_k.name >= min_k_count:
                checkout = True
        if checkout or current_k.name - start_k.name >= 200:
            self.order_module.close_order(self.backtest_info, order, df)

    @record_time
    def execute(self, *args, **kwargs):
        time_list = CRON_INTERVAL[self.interval]
        current_minute = datetime.now().minute
        if str(current_minute) not in time_list:
            raise DateTimeError()
        while True:
            period = 60 - datetime.now().second
            if period >= 5:
                time.sleep(0.2)
            else:
                break
        try:
            logger.info(f"symbol={self.symbol}开始执行")
            order = self.order_module.get_open_order(self.symbol, self.backtest_info)
            if order:
                self.exit_signal(order)
            else:
                self.entry_signal()
        except Exception as e:
            logger.exception(f"执行异常")
            raise e
