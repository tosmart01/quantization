# -- coding: utf-8 --
# @Time : 2023/12/12 16:11
# @Author : zhuo.wang
# @File : tools.py
import os
import pickle
import time
from datetime import datetime

import pandas as pd
import retry
from loguru import logger
from pandas import Timestamp

from client.binance_client import client
from schema.buy_info import InfoModel
from config.settings import CACHE_DIR


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
    return df


def get_color(value, is_end=False):
    if not is_end:
        return f'[{"red" if value >= 0 else "green"}]'
    else:
        return f'[/{"red" if value >= 0 else "green"}]'


@retry.retry(tries=30, delay=0.2)
def get_current_profit(code_list=None) -> tuple[float, dict, float]:
    data = client.futures_account()
    code_profit = {}
    for code in code_list:
        value = float([i for i in data['positions'] if i.get('symbol') == code][0]['unrealizedProfit'])
        code_profit[code] = value
    ratio = float(data['totalCrossUnPnl']) / float(data['totalMarginBalance'])
    return float(data['totalCrossUnPnl']), code_profit, ratio


def get_data(symbol: str):
    cache_path = os.path.join(CACHE_DIR, f"{symbol}.pkl")
    new_df = None
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as fp:
            cache_dict = pickle.load(fp)
        cache_df = cache_dict['df']
        cache_time = pd.to_datetime(cache_dict['time'])
        offset = (datetime.now() - cache_time).total_seconds() / 60
        if offset <= 30:
            data = client.futures_klines(symbol=symbol, limit=5, interval="15m", timeout=20)
            df = format_df(data, 'btc')
            new_df = pd.concat([cache_df, df], axis=0)
            new_df = new_df.drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)
    if new_df is None:
        data = client.futures_klines(symbol=symbol, limit=300, interval="15m", timeout=20)
        new_df = format_df(data, 'btc')
    with open(cache_path, 'wb') as fp:
        pickle.dump({'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'df': new_df}, fp)
    return new_df.iloc[-300:, ::].reset_index(drop=True)


@retry.retry(tries=30, delay=0.2)
def get_diff(A, B, div=1):
    btc_df = get_data(A)
    eth_df = get_data(B)
    normalized_difference = (btc_df['close'] * div - eth_df['close']) / eth_df['close']
    return normalized_difference


def get_rate(buy_info: InfoModel, current_num: float) -> str:
    if buy_info.win_info:
        target_price = buy_info.win_info.eq_number
        total_difference = abs(target_price - buy_info.first_num)
        current_length = abs(current_num - target_price)
        rate = abs(1 - current_length / total_difference)
        if buy_info.first_num <= current_num <= target_price:
            rate = rate
        else:
            rate = -rate
        return f"{rate:.2%}"
    return ""


def record_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.6f} seconds")
        return result

    return wrapper


def series_to_dict(series: pd.Series | dict) -> dict:
    res: dict = series.to_dict() if isinstance(series, pd.Series) else series.dict()
    for key, value in res.items():
        if isinstance(value, (Timestamp, datetime)):
            res[key] = value.strftime("%Y-%m-%d %H:%M:%S")
    return res
