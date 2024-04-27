# -- coding: utf-8 --
# @Time : 2023/12/12 16:11
# @Author : zhuo.wang
# @File : tools.py
import time
from datetime import datetime

import talib
import pandas as pd
from loguru import logger
from pandas import Timestamp

from config.settings import OPENING_THRESHOLD, ASTRINGENCY_THRESHOLD


def fill_consecutive_true(arr: list[bool], offset=20, ratio=0.9) -> list[bool]:
    if len(arr) < offset:
        return arr
    start = 0
    while start + offset <= len(arr):
        cut_arr = arr[start: start + offset]
        if sum(cut_arr) / offset >= ratio:
            arr[start: start + offset] = [True] * offset
            start += offset
        else:
            start += 1
    return arr


def add_band_fields(df: pd.DataFrame) -> pd.DataFrame:
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2,
                                                                         nbdevdn=2, matype=0)
    df['band_width'] = df['upper_band'] - df['lower_band']
    # 确定盘整区间
    df['short_term_avg_width'] = df['band_width'].rolling(window=30).mean()
    df['long_term_avg_width'] = df['band_width'].rolling(window=60).mean()
    df['band_width_ma'] = df['band_width'].rolling(window=30).mean()
    df['band_width_change'] = df['band_width'] / df['band_width_ma']
    df['consolidation'] = ((df['short_term_avg_width'] < df['long_term_avg_width'] * ASTRINGENCY_THRESHOLD)  # 短期宽度小于长期宽度的80%
                           & (df['band_width_change'].abs() < OPENING_THRESHOLD) #布林带开口
                           )
    df['consolidation'] = fill_consecutive_true(df['consolidation'])
    return df


def format_df(data, symbol) -> pd.DataFrame:
    data = [i[:6] for i in data]
    df = pd.DataFrame(
        data, columns=["date", "open", "high", "low", "close", "volume"]
    )
    df = df.astype(float)
    df["date"] = df["date"].apply(lambda x: datetime.fromtimestamp(x / 1000))
    df = df.drop_duplicates(["date"]).sort_values("date")
    df["pct_change"] = df["close"].pct_change() * 100
    df["symbol"] = symbol
    # 振幅
    df['tr'] = df['high'] - df['low']
    # 阳线阴线
    df['is_bull'] = df['close'] > df['open']
    # 去掉最后一行
    #     df = df.iloc[:-1, ::]
    df = add_band_fields(df)
    return df


def record_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.6f} seconds")
        return result

    return wrapper


def series_to_dict(series: pd.Series | dict, fields=None) -> dict:
    from schema.order_schema import OrderDataDict
    res: dict = series.to_dict() if isinstance(series, pd.Series) else series.dict()
    fields = list(OrderDataDict.model_fields.keys()) if not fields else fields
    data = {}
    for key, value in res.items():
        if isinstance(value, (Timestamp, datetime)):
            res[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        if key in fields:
            data[key] = value
    return res


def round_float_precision(num1, num2):
    # 获取num1的小数位数
    if isinstance(num1, float):
        precision = len(str(num1).split('.')[1])
        # 将num2的小数位数round成precision
        rounded_num2 = round(num2, precision)
        return rounded_num2
    return int(num2)