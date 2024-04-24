# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:24:26
# @Author: Donvink wuwukai
# @Site: 
# @File: m_head.py
# @Software: PyCharm
import time
from datetime import datetime
import pandas as pd

from common.log import logger
from common.tools import record_time
from config.settings import CRON_INTERVAL, MIN_TRADE_COUNT, NEAR_HIGH_K_COUNT, COMPARE_HIGH_K_COUNT, \
    CONSOLIDATION_HIGH_COUNT
from strategy.base import BaseStrategy
from strategy.tools import recent_kline_avg_amplitude, find_high_index, get_shadow_line_ratio, \
    check_high_value_in_range, adapt_by_percent, get_entry_signal_low_point
from order.enums import DirectionEnum, SideEnum
from schema.order_schema import OrderModel
from exceptions.custom_exceptions import DateTimeError


class MHeadStrategy(BaseStrategy):

    def check_near_volume(self, current_k: pd.Series, compare_k: pd.Series, df: pd.DataFrame) -> bool:
        current_volume = df.loc[current_k.name - 1: current_k.name + 1, 'volume'].mean()
        compare_volume = df.loc[compare_k.name - 1: compare_k.name + 1, 'volume'].mean()
        return current_volume <= compare_volume

    def check_consolidation(self, high_index_list: list[int], df: pd.DataFrame, last_high_k: pd.Series) -> bool:
        k = df.iloc[-1]
        if k.consolidation:
            start = df.loc[(df.date <= k.date) & (df.consolidation == False)].iloc[-1].name + 1
            band_list = [i for i in high_index_list if i >= start]
            if len(band_list) >= CONSOLIDATION_HIGH_COUNT:
                return False
            elif len(band_list) == 1 and band_list[-1] == last_high_k.name:
                return False
            else:
                return True
        return False

    def check_pct_change_range(self, df: pd.DataFrame, compare_high_k: pd.Series, last_high_k: pd.Series) -> bool:
        last_k = df.iloc[-1]
        low_value = df.loc[compare_high_k.name: last_k.name, 'low'].min()
        decline_percent = adapt_by_percent(df)
        left_low_point = get_entry_signal_low_point(df, compare_high_k)
        if left_low_point is not None:
            if last_k.name - left_low_point.name >= 20:
                low_value = min(left_low_point.low, low_value)
        pct_change_verify = (max(last_k.high, last_high_k.high) - low_value) / low_value > decline_percent
        return pct_change_verify

    def find_enter_point(self, compare_high_index: int, df: pd.DataFrame, high_index_list: list) -> tuple[
        bool, pd.Series]:
        compare_high_k = df.loc[high_index_list[compare_high_index]]
        last_high_k = df.loc[high_index_list[-1]]
        last_k: pd.Series = df.iloc[-1]
        if last_k.close >= compare_high_k.high:
            return False, last_k
        # 当前k线距离前高太远排除
        if not (last_k.name - last_high_k.name <= NEAR_HIGH_K_COUNT):
            return False, last_k
        if self.check_consolidation(high_index_list, df, last_high_k):
            return False, last_k
        AM = recent_kline_avg_amplitude(df.loc[compare_high_k.name - 9: compare_high_k.name])
        ge_last_high_k_list = []
        near_high_list = []
        is_near_high_k = last_k.name - last_high_k.name <= NEAR_HIGH_K_COUNT
        if self.check_pct_change_range(df, compare_high_k, last_high_k):
            overtop = False
            mid = df.loc[last_high_k.name - 4: last_high_k.name, 'close'].mean()
            for k in df.loc[last_high_k.name: last_k.name].itertuples():
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
                if k.high > (compare_high_k.high + 1.5 * AM) and is_near_high_k:
                    overtop = True
                if verify and k.high > compare_high_k.high:
                    ge_last_high_k_list.append(True)
                near_high_list.append(verify)
            verify_length = len(list(filter(None, near_high_list)))
            if verify_length >= 1 and not overtop and len(ge_last_high_k_list) <= 2:
                # 阴线命中
                if last_k.close < last_k.open:
                    # 命中k线涨幅限制
                    if last_k.close - last_k.open <= 1.5 * AM:
                        # if len(high_index_list) >=3:
                        # tr = df.loc[high_index_list[-3]: high_index_list[-1], 'high'].max() / df.loc[high_index_list[-3]: high_index_list[-1], 'low'].min() - 1
                        # tr = abs(df.loc[high_index_list[-3], 'high'] / df.loc[high_index_list[-1], 'high'] - 1)
                        # if tr >= 0.032:
                        # if not self.check_consolidation(high_index_list, df, last_high_k):
                        return (True, compare_high_k)
        return False, compare_high_k

    def check_near_prior_high_point(self, df: pd.DataFrame) -> tuple[bool, pd.Series]:
        high_index_list = find_high_index(df)
        if len(high_index_list) < 2:
            return False, df.iloc[1]
        compare_high_list = [-i - 2 for i in range(len(high_index_list) - 1)][:COMPARE_HIGH_K_COUNT]
        for index in compare_high_list:
            verify, compare_high_k = self.find_enter_point(index, df, high_index_list)
            if verify:
                return verify, compare_high_k
        return False, df.loc[0]

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
        min_k_count = MIN_TRADE_COUNT
        start_k = df.loc[df['date'] == order.start_data.date].iloc[0]
        AM = recent_kline_avg_amplitude(df.loc[current_k.name - 9: current_k.name])
        trade_days = current_k.name - start_k.name >= min_k_count
        if order.low_point is not None and trade_days:
            # 近3跟k线接近前期低点，并且当前k线收阳线，平仓
            for row in df.loc[current_k.name - 2: current_k.name].itertuples():
                if abs(row.low - order.low_point.low) <= AM * 0.10 and current_k.is_bull:
                    checkout = True
                    break
                # 如果已经低于前期低点，收阳线平仓
                if row.low < order.low_point.low and current_k.is_bull:
                    checkout = True
                    break
        if not checkout:
            count = 0
            for row in df.loc[current_k.name - 2: current_k.name].itertuples():
                if row.close - row.open > 0:
                    count += 1
            if count >= 3 and trade_days:
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
