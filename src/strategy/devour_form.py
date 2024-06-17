# -- coding: utf-8 --
# @Time : 2024/6/17 11:24
# @Author : PinBar
# @File : devour_form.py
import pandas as pd

from common.log import logger
from order.enums import SideEnum, DirectionEnum
from schema.order_schema import OrderModel, OrderDataDict
from .base import BaseStrategy
from enum import Enum
from exceptions.custom_exceptions import StrategyNotMatchError

from .strategy_helper import find_high_index, find_low_index


class TradeEnum(Enum):
    BULL_TRADE = 100
    BEAR_TRADE = 200
    NOT_TRADE = 0


class DevourFormStrategy(BaseStrategy):
    check_devour_count = 2

    def get_trade(self, df: pd.DataFrame, weight: float, period: int = 15) -> TradeEnum:
        bull = df.tail(period).loc[df.is_bull]
        bear = df.tail(period).loc[~df.is_bull]
        bull_value = (bull.close - bull.open).sum()
        bear_value = (bear.open - bear.close).sum()
        if bull_value > bear_value:
            if bear_value and bull_value / bear_value >= weight:
                return TradeEnum.BULL_TRADE
        if bear_value > bull_value:
            if bull_value and bear_value / bull_value >= weight:
                return TradeEnum.BEAR_TRADE
        return TradeEnum.NOT_TRADE

    def is_big_candle(self, df: pd.DataFrame, period: int = 15, weight: float = 0,
                      current_candle: pd.Series = None) -> bool:
        data = df.tail(period)
        candle_body_mean = (data.open - data.close).abs().mean()
        if abs(current_candle.close - current_candle.open) / candle_body_mean >= weight:
            return True
        return False

    def check_point(self, df: pd.DataFrame, current_candle: pd.Series, trade: TradeEnum) -> SideEnum:
        current_k: pd.Series = df.iloc[-1]
        big_candle = self.is_big_candle(df, weight=1.5, current_candle=current_candle)
        if big_candle:
            if trade == TradeEnum.BEAR_TRADE and not current_candle.is_bull and current_k.is_bull:
                if current_k.close > current_candle.open:
                    return SideEnum.BUY
            if trade == TradeEnum.BULL_TRADE and current_candle.is_bull and not current_k.is_bull:
                if current_k.close < current_candle.open:
                    return SideEnum.SELL

    def get_stop_price(self, current_candle: pd.Series, current_k: pd.Series, side: SideEnum):
        if side == SideEnum.BUY:
            return current_candle.low # min(current_candle.low, current_k.low)
        if side == SideEnum.SELL:
            return current_candle.high # max(current_candle.high, current_k.high)

    def get_take_price(self, df: pd.DataFrame, stop_price: float, side: SideEnum, open_price: float):
        if side == SideEnum.SELL:
            low_index = find_low_index(df, distance=30, prominence=5)[-1]
            low = df.loc[low_index]
            loss_price = (stop_price - open_price)
            take_price = (open_price - low.low)
            if take_price / loss_price <= 1.5:
                raise StrategyNotMatchError()
            print(take_price / loss_price)
            return low.low
        if side == SideEnum.BUY:
            high_index = find_high_index(df, distance=30, prominence=5)[-1]
            high = df.loc[high_index]
            loss_price = (open_price - stop_price)
            take_price = high.high - open_price
            if take_price / loss_price <= 1.5:
                raise StrategyNotMatchError()
            print(take_price / loss_price)
            return high.high

    def check_condition(self, df: pd.DataFrame, trade: TradeEnum, ):
        current_k: pd.Series = df.iloc[-1]
        index_list = list(range(-self.check_devour_count - 1, -1))[::-1]
        for index in index_list:
            current_candle: pd.Series = df.iloc[index]
            if abs(current_candle['pct_change']) <= 0.3:
                continue
            side = self.check_point(df, current_candle, trade)
            if side is not None:
                stop_price = self.get_stop_price(current_candle, current_k, side)
                try:
                    take_price = self.get_take_price(df, stop_price, side, open_price=current_k.close)
                except StrategyNotMatchError:
                    continue
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
                    take_price=take_price,
                )
                order = self.order_module.create_order(
                    backtest=self.backtest_info,
                    df=df,
                    usdt=self.buy_usdt,
                    order_schema=order_schema,
                )
                logger.info(f"条件单出现, symbol={self.symbol}, 日期={df.iloc[-1]['date']}")
                return order

    def entry_signal(self, *args, **kwargs):
        df = self.data_module.get_futures_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        trade1 = self.get_trade(df, weight=2, period=15)
        if trade1 != TradeEnum.NOT_TRADE:
            trade = trade1
        else:
            trade2 = self.get_trade(df, weight=2, period=30)
            trade = trade2
        if trade == TradeEnum.NOT_TRADE:
            return
        self.check_condition(df, trade)

    def exit_signal(self, order: OrderModel):
        df = self.data_module.get_futures_klines(self.symbol, self.interval, backtest_info=self.backtest_info)
        current_k = df.iloc[-1]
        stop_loss = self.order_module.check_stop_loss(order, df, order.side.direction(), self.backtest_info)
        if stop_loss:
            return
        take_price = order.take_price
        checkout = False
        for row in df.tail(3).itertuples():
            if order.side == SideEnum.BUY:
                if row.high >= take_price and not current_k.is_bull:
                    checkout = True
                    break
            if order.side == SideEnum.SELL:
                if row.low <= take_price and current_k.is_bull:
                    checkout = True
                    break
        k_count = (current_k.date - order.start_time).total_seconds() / 3600
        if checkout:
            return self.order_module.close_order(self.backtest_info, order, df)
        if k_count >= 50:
            return self.order_module.close_order(self.backtest_info, order, df)
