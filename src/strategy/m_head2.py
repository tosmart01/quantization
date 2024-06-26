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
from common.tools import record_time, round_float_precision
from config.settings import CRON_INTERVAL, MIN_TRADE_COUNT, NEAR_HIGH_K_COUNT, COMPARE_HIGH_K_COUNT, \
    CONSOLIDATION_HIGH_COUNT, M_DECLINE_PERCENT, MAX_STOP_LOSS_RATIO, MAX_STOP_LOSS_PERCENT
from strategy.base import BaseStrategy
from strategy.strategy_helper import recent_kline_avg_amplitude, find_high_index, get_shadow_line_ratio, \
    check_high_value_in_range, adapt_by_percent, get_m_head_entry_low_point, get_m_head_low_point, get_value_from_range
from order.enums import DirectionEnum, SideEnum
from schema.order_schema import OrderModel, OrderDataDict
from exceptions.custom_exceptions import DateTimeError


class MHeadStrategy(BaseStrategy):

    @staticmethod
    def adapt_loss_ratio(df: pd.DataFrame) -> float:
        return (df.tr.mean() / df.close.mean()) * (M_DECLINE_PERCENT * MAX_STOP_LOSS_RATIO)

    def get_stop_loss_price(self, start_data: pd.Series, compare_data: pd.Series, df: pd.DataFrame) -> float:
        stop_ratio = self.adapt_loss_ratio(df)
        compare_high = max(compare_data.high, start_data.high)
        pct_change = (compare_high - start_data.close) / start_data.close
        if compare_high > start_data.close and pct_change <= stop_ratio:
            # 根据波动率自适应止损价
            close_price = compare_high
        elif start_data.close < compare_data.close:
            # 使用对比k收盘价止损
            close_price = compare_data.close
        else:
            close_price = start_data.open
            if (start_data.high - start_data.close) / start_data.close <= stop_ratio:
                close_price = start_data.high
                logger.info(
                    f"{self.symbol}, "
                    f"开盘价止损,{(close_price - start_data.close) / start_data.close:.2%}, {start_data.date=}")
        # 设置最大止损
        if (close_price - start_data.close) / start_data.close >= MAX_STOP_LOSS_PERCENT:
            close_price = min((close_price - start_data.close) / 2 + start_data.close,
                              start_data.close * (1 + MAX_STOP_LOSS_PERCENT) * 1.1
                              )
            close_price = round_float_precision(start_data.close, close_price)
            logger.info(
                f"{self.symbol}设置最大止损={(close_price - start_data.close) / start_data.close:.2%},  {start_data.date=}")
        return close_price

    @staticmethod
    def check_near_volume(current_k: pd.Series, compare_k: pd.Series, df: pd.DataFrame) -> bool:
        current_volume = df.loc[current_k.name - 1: current_k.name + 1, 'volume'].mean()
        compare_volume = df.loc[compare_k.name - 1: compare_k.name + 1, 'volume'].mean()
        return current_volume <= compare_volume

    @staticmethod
    def check_consolidation(high_index_list: list[int], df: pd.DataFrame, last_high_k: pd.Series) -> bool:
        k = df.iloc[-1]
        if k.consolidation:
            start = df.loc[(df.date <= k.date) & (~df.consolidation)].iloc[-1].name + 1
            band_list = [i for i in high_index_list if i >= start]
            if len(band_list) >= CONSOLIDATION_HIGH_COUNT:
                return False
            elif len(band_list) == 1 and band_list[-1] == last_high_k.name:
                return False
            else:
                return True
        return False

    @staticmethod
    def check_pct_change_range(df: pd.DataFrame, compare_high_k: pd.Series, last_high_k: pd.Series) -> bool:
        last_k = df.iloc[-1]
        low_value = df.loc[compare_high_k.name: last_k.name, 'low'].min()
        decline_percent = adapt_by_percent(df)
        left_low_point = get_m_head_entry_low_point(df, compare_high_k)
        if left_low_point is not None:
            if last_k.name - left_low_point.name >= 23:
                low_value = min(left_low_point.low, low_value)
        pct_change_verify = (max(last_k.high, last_high_k.high) - low_value) / low_value > decline_percent
        return pct_change_verify

    def find_enter_point(self, compare_high_k: pd.Series, df: pd.DataFrame, last_high_k: pd.Series) -> bool:
        last_k: pd.Series = df.iloc[-1]
        # 阴线命中
        if last_k.is_bull:
            return False
        if last_k.close >= compare_high_k.high:
            return False
        # 当前k线距离前高太远排除
        if not (last_k.name - last_high_k.name <= NEAR_HIGH_K_COUNT):
            return False
        # if self.check_consolidation(high_index_list, df, last_high_k):
        #     return False, last_k
        am = recent_kline_avg_amplitude(df.loc[compare_high_k.name - 9: compare_high_k.name])
        ge_last_high_k_list = []
        near_high_list = []
        is_near_high_k = last_k.name - last_high_k.name <= NEAR_HIGH_K_COUNT
        if self.check_pct_change_range(df, compare_high_k, last_high_k):
            overtop = False
            mid = df.loc[last_high_k.name - 4: last_high_k.name, 'close'].mean()
            for k in df.loc[last_high_k.name: last_k.name].itertuples():
                current_am = recent_kline_avg_amplitude(df.loc[k.Index - 9: k.Index])
                # 命中价格区间
                verify = check_high_value_in_range(k, compare_high_k, am)
                shadow_ratio = get_shadow_line_ratio(k)
                # 上引线过长排除
                if shadow_ratio >= 0.5 and current_am * 1.5 < k.high - k.low:
                    verify = False
                if k.high < mid:
                    verify = False
                # 涨幅过大排除
                if k.high > (compare_high_k.high + 1.5 * am) and is_near_high_k:
                    overtop = True
                if verify and k.high > compare_high_k.high:
                    ge_last_high_k_list.append(True)
                near_high_list.append(verify)
            verify_length = len(list(filter(None, near_high_list)))
            if verify_length >= 1 and not overtop and len(ge_last_high_k_list) <= 2:
                # 命中k线涨幅限制
                if last_k.close - last_k.open <= 1.5 * am:
                    return True

    def get_min_profit_loss_ratio(self, df: pd.DataFrame) -> float:
        volatility = df.tr.mean()
        profit_loss_map = [
            (0, 20, 1,),
            (20, 40, 2,),
            (40, 60, 3),
            (60, 1000, 3),
        ]
        return get_value_from_range(profit_loss_map, volatility)
    def get_take_profit_price_range(self, df, left_bottom, right_bottom, head_point, current_k) -> tuple[float, float]:
        min_profit_loss_ratio = self.get_min_profit_loss_ratio(df)
        max_take_price = right_bottom.high - (right_bottom.high - head_point.low) * 1.8
        if left_bottom.high > right_bottom.high:
            profit_loss_ratio = (current_k.close - head_point.low) / (right_bottom.high - current_k.close)
            take_price = head_point.low
            if profit_loss_ratio <= min_profit_loss_ratio:
                take_price = current_k.close - (right_bottom.high - current_k.close) * min_profit_loss_ratio
                take_price = max(max_take_price, take_price)
        else:
            profit_loss_ratio = (current_k.close - head_point.close) / (right_bottom.high - current_k.close)
            take_price = head_point.close
            if profit_loss_ratio <= min_profit_loss_ratio:
                take_price = current_k.close - (right_bottom.high - current_k.close) * min_profit_loss_ratio
                take_price = max(max_take_price, take_price)
        # if small_volatility:
        #     take_price = head_point.close
        left = current_k.close - (current_k.close - take_price) * 0.75
        return left, take_price

    def check_near_prior_high_point(self, df: pd.DataFrame) -> OrderModel:
        high_index_list = find_high_index(df, prominence=3)
        if len(high_index_list) >= 2:
            compare_high_list = [-i - 2 for i in range(len(high_index_list) - 1)][:COMPARE_HIGH_K_COUNT]
            last_high_k = df.loc[high_index_list[-1]]
            current_k = df.iloc[-1]
            for index in compare_high_list:
                compare_high_k = df.loc[high_index_list[index]]
                verify = self.find_enter_point(compare_high_k, df, last_high_k)
                if verify:
                    low_point = df.loc[df.loc[compare_high_k.name: last_high_k.name, 'low'].idxmin()]
                    stop_price = self.get_stop_loss_price(current_k, compare_high_k, df)
                    _, take_price = self.get_take_profit_price_range(df, compare_high_k, last_high_k, low_point, current_k)
                    expected_profit = (current_k.close - take_price) / current_k.close
                    expected_loss = (stop_price - current_k.close) / current_k.close
                    profit_loss_ratio = expected_profit / expected_loss
                    if profit_loss_ratio > 1:
                        return OrderModel(symbol=self.symbol,
                                          active=True, start_time=current_k.date,
                                          start_data=OrderDataDict(**current_k.to_dict()),
                                          open_price=current_k.close, stop_price=stop_price,
                                          low_point=OrderDataDict(**low_point.to_dict()),
                                          interval=self.interval,
                                          compare_data=OrderDataDict(**compare_high_k.to_dict()),
                                          side=SideEnum.SELL, leverage=self.leverage,
                                          last_high_data=OrderDataDict(**last_high_k.to_dict())
                                          )

    def entry_signal(self) -> OrderModel:
        df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        order_schema = self.check_near_prior_high_point(df)
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
        stop_loss = self.order_module.check_stop_loss(order, df, DirectionEnum.SHORT, self.backtest_info)
        if stop_loss:
            return
        checkout = False
        current_k: pd.Series = df.iloc[-1]
        min_k_count = MIN_TRADE_COUNT
        start_k = df.loc[df['date'] == order.start_data.date].iloc[0]
        am = recent_kline_avg_amplitude(df.loc[current_k.name - 9: current_k.name])
        trade_days = current_k.name - start_k.name >= min_k_count
        left, take_price = self.get_take_profit_price_range(df, order.compare_data,
                                                         order.last_high_data, order.low_point, order.start_data)
        if order.low_point is not None and trade_days:
            # 近3跟k线接近前期低点，并且当前k线收阳线，平仓
            for row in df.loc[current_k.name - 2: current_k.name].itertuples():
                if row.low <= left and current_k.is_bull:
                    checkout = True
                    break
                # 如果已经低于前期低点，收阳线平仓
                if row.low < left and current_k.is_bull:
                    checkout = True
                    break
        if not checkout:
            count = 0
            for row in df.loc[current_k.name - 2: current_k.name].itertuples():
                if row.close - row.open > 0:
                    count += 1
            if count >= 3 and trade_days:
                checkout = True
        if checkout or current_k.name - start_k.name >= 60:
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
