# -*- coding = utf-8 -*-
# @Time: 2024-04-05 12:31:32
# @Author: Donvink wuwukai
# @Site: 
# @File: tools.py
# @Software: PyCharm
import pandas as pd
from scipy.signal import find_peaks

from config.settings import MAX_VALUE_PERIOD, MIN_VALUE_PERIOD, MIN_TRADE_COUNT, M_DECLINE_PERCENT
from schema.order_schema import OrderModel



def adapt_by_percent(df: pd.DataFrame):
    # return (df.tail(40).tr.mean() / df.tail(40).close.mean()) * M_DECLINE_PERCENT
    return (df.tr.mean() / df.close.mean()) * M_DECLINE_PERCENT


def recent_kline_avg_amplitude(data: pd.DataFrame) -> float:
    """
    近10k 振幅均值：AM
    @param data: pd.DataFrame
    """
    return ((data['high'] - data['low'])).mean()


def average_volume_around_high_point(data: pd.DataFrame) -> float:
    """
    高点周围三根k线成交量平均值
    @param data:  pd.DataFrame
    @return:
    """
    ...


def check_high_value_in_range(k: pd.Series, compare_k: pd.Series, AM: float, ) -> bool:
    """
    验证当前k是否在对比k的高点区间内
    @param k: 当前k
    @param compare_k: 对比k
    @param AM: 近N日价格波动区间
    @return:
    """
    verify = (compare_k.high - 0.65 * AM) <= k.high <= (compare_k.high + 0.85 * AM)
    return verify


def find_high_index(df: pd.DataFrame, distance: int = MAX_VALUE_PERIOD, prominence=0) -> list[int]:
    """
    计算数据内局部最大值索引, 为了避免最后一个值是最大值时无法找到，
    尾部插入一个值, 为最后一个值 减去万分之一
    @param df: pd.DataFrame
    @param distance: 计算极值的区间
    @return: 极值的索引列表
    """
    find_series: pd.Series = df['high']
    insert_tail = find_series.iloc[-1] - find_series.iloc[-1] * 0.0001
    insert_series = pd.Series([insert_tail], index=[find_series.index[-1] + 1])
    find_series: pd.Series = pd.concat([find_series, insert_series])
    find_index_list: list[int] = find_peaks(find_series, distance=distance, prominence=prominence)[0].tolist()
    offset = int(distance / 3)
    new_index_list = []
    for index in find_index_list:
        left = index - offset
        right = index + offset
        round_data: pd.Series = df.loc[left: right + 1, 'high']
        if not round_data.empty:
            max_value = round_data.max()
            if max_value == df.loc[index, 'high']:
                new_index_list.append(index)
    # if len(new_index_list) > 1:
    #     k = df.loc[new_index_list[-1]]
    #     AM = recent_kline_avg_amplitude(df.loc[k.name - 9: k.name])
    #     last_index = new_index_list.pop()
    #     distant_high_list: pd.Series = abs(df.loc[(df.index.isin(new_index_list[:-1])), 'high'] - k.high).sort_values()[:3]
    #     distant_high_list = distant_high_list.sort_index()
    #     # 添加较远距离高点到列表末尾, 优先考虑远距离高点
    #     for index in distant_high_list.index:
    #         if index not in new_index_list[-3:]:
    #             new_k: pd.Series = df.loc[index]
    #             # 判定高点是距离当前k线较远的k线高点
    #             if (k.date - new_k.date).total_seconds() >= DECLINE_HIGH_TIME * 60:
    #                 if check_high_value_in_range(k, new_k, AM):
    #                     if new_k.high >= df.loc[index + 1: k.name - 1, 'high'].max():
    #                         new_index_list.remove(index)
    #                         new_index_list.append(index)
    #                         break
    #     new_index_list.append(last_index)
    return new_index_list


def find_low_index(df: pd.DataFrame, distance: int = MIN_VALUE_PERIOD) -> list[int]:
    """
    计算数据内局部最小值索引
    @param df: pd.DataFrame
    @param distance: 计算极值的区间
    @return: 极值的索引列表
    """
    find_index_list: list[int] = find_peaks(-df['low'], distance=distance)[0].tolist()
    offset = int(distance / 3)
    new_index_list = []
    for index in find_index_list:
        left = index - offset
        right = index + offset
        round_data: pd.Series = df.loc[left: right + 1, 'low']
        if not round_data.empty:
            min_value = round_data.min()
            if min_value == df.loc[index, 'low']:
                new_index_list.append(index)
    return new_index_list


def get_shadow_line_ratio(data: pd.Series) -> float:
    try:
        if data.close >= data.open:
            shadow = data.high - data.close
            return shadow / (data.high - data.low)
        else:
            shadow = data.high - data.open
            return shadow / (data.high - data.low)
    except ZeroDivisionError:
        return 0


def get_low_point(df: pd.DataFrame, order: OrderModel) -> pd.Series | None:
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
    if abs(start_k.name - low_point.name) <= MIN_TRADE_COUNT:
        min_index = df.loc[(df.date > order.compare_data.date) & (df.date < order.start_data.date), 'low'].idxmin()
        min_point: pd.Series = df.loc[min_index]
        if min_point.low <= low_point.low:
            low_point = min_point
    # if (order.compare_data.high - low_point.low) / low_point.low > M_DECLINE_PERCENT * 2:
    #     low_point.low = order.start_data.close * (1 - M_DECLINE_PERCENT * 1.5)
    return low_point


def get_entry_signal_low_point(df: pd.DataFrame, compare_k: pd.Series) -> pd.Series:
    low_index_list = find_low_index(df)
    low_df = df.loc[low_index_list]
    low_point_left = low_df.loc[low_df['date'] < compare_k.date]
    if not low_point_left.empty:
        left_low_point = low_point_left.iloc[-1]
        return left_low_point
