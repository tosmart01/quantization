# -*- coding = utf-8 -*-
# @Time: 2024-04-05 12:31:32
# @Author: Donvink wuwukai
# @Site: 
# @File: tools.py
# @Software: PyCharm
import pandas as pd
from scipy.signal import find_peaks

from config.settings import MAX_VALUE_PERIOD, MIN_VALUE_PERIOD


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


def find_high_index(df: pd.DataFrame, distance: int = MAX_VALUE_PERIOD, prominence=None) -> list[int]:
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
    # if len(new_index_list) >= 2 and new_index_list[-1] != len(df) - 1:
    #     mean_price_change = (df.tail(10)['high'] - df.tail(10)['low']).mean()
    #     if (df.iloc[-1]['high'] - df.loc[new_index_list[-1], 'high']) <= mean_price_change:
    #         new_index_list.append(len(df) - 1)
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
