# -*- coding = utf-8 -*-
# @Time: 2024-04-05 12:31:32
# @Author: Donvink wuwukai
# @Site: 
# @File: tools.py
# @Software: PyCharm
import pandas as pd
from scipy.signal import find_peaks

from config.settings import MAX_VALUE_PERIOD, MIN_VALUE_PERIOD, MIN_TRADE_COUNT, M_DECLINE_PERCENT


def adapt_by_percent(df: pd.DataFrame):
    # return (df.tail(40).tr.mean() / df.tail(40).close.mean()) * M_DECLINE_PERCENT
    return (df.tr.mean() / df.close.mean()) * M_DECLINE_PERCENT


def recent_kline_avg_amplitude(data: pd.DataFrame) -> float:
    """
    近10k 振幅均值：AM
    @param data: pd.DataFrame
    """
    return (data['high'] - data['low']).mean()


def check_high_value_in_range(k: pd.Series, compare_k: pd.Series, am: float, ) -> bool:
    """
    验证当前k是否在对比k的高点区间内
    @param k: 当前k
    @param compare_k: 对比k
    @param am: 近N日价格波动区间
    @return:
    """
    verify = (compare_k.high - 0.65 * am) <= k.high <= (compare_k.high + 0.85 * am)
    return verify


def find_high_index(df: pd.DataFrame, distance: int = MAX_VALUE_PERIOD, prominence=0) -> list[int]:
    """
    计算数据内局部最大值索引, 为了避免最后一个值是最大值时无法找到，
    尾部插入一个值, 为最后一个值 减去万分之一
    @param df: pd.DataFrame
    @param distance: 计算极值的区间
    @param prominence: 计算极值的区间
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
    return new_index_list


def find_low_index(df: pd.DataFrame, distance: int = MIN_VALUE_PERIOD) -> list[int]:
    """
    计算数据内局部最小值索引
    @param df: pd.DataFrame
    @param distance: 计算极值的区间
    @return: 极值的索引列表
    """
    find_series: pd.Series = df['low']
    insert_tail = find_series.iloc[-1] + find_series.iloc[-1] * 0.0001
    insert_series = pd.Series([insert_tail], index=[find_series.index[-1] + 1])
    find_series: pd.Series = pd.concat([find_series, insert_series])
    find_index_list: list[int] = find_peaks(-find_series, distance=distance)[0].tolist()
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


def get_m_head_low_point(df: pd.DataFrame, compare_k: pd.Series, current_k: pd.Series) -> pd.Series | None:
    low_index_list = find_low_index(df)
    low_df = df.loc[low_index_list]
    low_point_left = low_df.loc[low_df['date'] < compare_k.date]
    low_point_right = low_df.loc[low_df['date'] > compare_k.date]
    low_point = None
    if not low_point_right.empty:
        low_point = low_point_right.iloc[0]
    elif not low_point_left.empty:
        low_point = low_point_left.iloc[-1]
    start_k = df.loc[df['date'] == current_k.date].iloc[-1]
    if abs(start_k.name - low_point.name) <= MIN_TRADE_COUNT:
        min_index = df.loc[(df.date > compare_k.date) & (df.date < current_k.date), 'low'].idxmin()
        min_point: pd.Series = df.loc[min_index]
        if min_point.low <= low_point.low:
            low_point = min_point
    # if (order.compare_data.high - low_point.low) / low_point.low > M_DECLINE_PERCENT * 2:
    #     low_point.low = order.start_data.close * (1 - M_DECLINE_PERCENT * 1.5)
    return low_point


def get_m_head_entry_low_point(df: pd.DataFrame, compare_k: pd.Series) -> pd.Series:
    low_index_list = find_low_index(df)
    low_df = df.loc[low_index_list]
    low_point_left = low_df.loc[low_df['date'] < compare_k.date]
    if not low_point_left.empty:
        left_low_point = low_point_left.iloc[-1]
        return left_low_point
