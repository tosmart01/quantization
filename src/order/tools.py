# -*- coding = utf-8 -*-
# @Time: 2024-04-14 1:02:44
# @Author: Donvink wuwukai
# @Site: 
# @File: tools.py
# @Software: PyCharm
import pandas as pd

from config.settings import MAX_STOP_LOSS_RATIO, M_DECLINE_PERCENT
from schema.order_schema import OrderModel


def adapt_loss_ratio(df: pd.DataFrame) -> float:
    return (df.tr.mean() / df.close.mean()) * (M_DECLINE_PERCENT * MAX_STOP_LOSS_RATIO)


def get_stop_loss_price(order: OrderModel, current_k: pd.Series, df: pd.DataFrame) -> float:
    stop_ratio = adapt_loss_ratio(df)
    compare_high = max(order.compare_data.high, order.start_data.high)
    pct_change = (compare_high - order.start_data.close) / order.start_data.close
    if pct_change <= stop_ratio:
        close_price = compare_high
    elif order.start_data.close < order.compare_data.close:
        close_price = order.compare_data.close
    else:
        close_price = order.start_data.open
        if (order.start_data.high - order.start_data.close) / order.start_data.close <= stop_ratio:
            close_price = order.start_data.high
            print( f"测试止损, start_time={order.start_data.date}, end_date={current_k.date},pct_change={order.start_data.pct_change}")
    return close_price
