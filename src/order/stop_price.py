# -*- coding = utf-8 -*-
# @Time: 2024-04-14 1:02:44
# @Author: Donvink wuwukai
# @Site: 
# @File: tools.py
# @Software: PyCharm
import pandas as pd

from common.log import logger
from common.tools import round_float_precision
from config.settings import MAX_STOP_LOSS_RATIO, M_DECLINE_PERCENT, MAX_STOP_LOSS_PERCENT
from schema.order_schema import OrderModel


def adapt_loss_ratio(df: pd.DataFrame) -> float:
    return (df.tr.mean() / df.close.mean()) * (M_DECLINE_PERCENT * MAX_STOP_LOSS_RATIO)


def get_stop_loss_price(order: OrderModel, current_k: pd.Series, df: pd.DataFrame) -> float:
    stop_ratio = adapt_loss_ratio(df)
    compare_high = max(order.compare_data.high, order.start_data.high)
    pct_change = (compare_high - order.start_data.close) / order.start_data.close
    if compare_high > order.start_data.close and pct_change <= stop_ratio:
        # 根据波动率自适应止损价
        close_price = compare_high
    elif order.start_data.close < order.compare_data.close:
        # 使用对比k收盘价止损
        close_price = order.compare_data.close
    else:
        close_price = order.start_data.open
        if (order.start_data.high - order.start_data.close) / order.start_data.close <= stop_ratio:
            close_price = order.start_data.high
            logger.info(f"{order.symbol}, 开盘价止损,{(close_price - order.start_data.close) / order.start_data.close:.2%}, {order.start_time=}")
    # 设置最大止损
    if (close_price - order.start_data.close) / order.start_data.close >= MAX_STOP_LOSS_PERCENT:
        close_price = min((close_price - order.start_data.close) / 2 + order.start_data.close,
                          order.start_data.close * (1 + MAX_STOP_LOSS_PERCENT) * 1.1
                          )
        close_price = round_float_precision(order.start_data.close, close_price)
        logger.info(f"{order.symbol}设置最大止损={(close_price - order.start_data.close) / order.start_data.close:.2%},  {order.start_time=}")
    return close_price
