# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:58:04
# @Author: Donvink wuwukai
# @Site: 
# @File: dataset.py
# @Software: PyCharm
import pandas as pd
from retry import retry

from schema.backtest import Backtest
from config.settings import TRADE_MAX_INTERVAL
from client.binance_client import client
from common.tools import format_df, add_band_fields
from exceptions.custom_exceptions import TestEndingError


class DataModule:

    @retry(tries=3, delay=3)
    def spot_fetch(self, symbol, interval, limit) -> list[list]:
        data = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        return data

    @retry(tries=3, delay=3)
    def futures_fetch(self, symbol, interval, limit) -> list[list]:
        data = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        return data

    def get_futures_klines(self, symbol: str, interval: str = '5m', limit: int = TRADE_MAX_INTERVAL,
                           backtest_info: Backtest = None) -> pd.DataFrame:

        if backtest_info.open_back:
            return self.get_fake_futures_klines(backtest_info)
        data = self.futures_fetch(symbol, interval, limit)
        df = format_df(data, symbol)
        return df

    def get_klines(self, symbol: str, interval: str = '5m', limit: int = TRADE_MAX_INTERVAL,
                   backtest_info: Backtest = None) -> pd.DataFrame:

        if backtest_info.open_back:
            return self.get_fake_klines(backtest_info)
        data = self.spot_fetch(symbol, interval, limit)
        df = format_df(data, symbol)
        return df

    @staticmethod
    def get_fake_klines(backtest_info: Backtest) -> pd.DataFrame:
        df = backtest_info.df.loc[backtest_info.start_offset: backtest_info.end_offset].reset_index(drop=True)
        if df.empty or backtest_info.end_offset > len(backtest_info.df):
            raise TestEndingError()
        backtest_info.start_offset += 1
        backtest_info.end_offset += 1
        return df

    @staticmethod
    def get_fake_futures_klines(backtest_info: Backtest) -> pd.DataFrame:
        df = backtest_info.df.loc[backtest_info.start_offset - 1: backtest_info.end_offset - 1].reset_index(drop=True)
        if df.empty or backtest_info.end_offset - 1 > len(backtest_info.df):
            raise TestEndingError()
        future_df = backtest_info.future_df
        return future_df.loc[(future_df.date >= df.date.iloc[0]) & (future_df.date <= df.date.iloc[-1])].reset_index(drop=True)

    @staticmethod
    def load_fake_klines(backtest_path: str) -> pd.DataFrame:
        df = pd.read_pickle(backtest_path)
        df['tr'] = df['high'] - df['low']
        df['is_bull'] = df['close'] > df['open']
        df['entity'] = (df['close'] - df['open']).abs()
        df = df.loc[(df['date'] >= '2021-01-01 00:00:00') & (df['date'] < '2023-12-28 23:30:00') ].reset_index(drop=True)
        df = add_band_fields(df)
        return df.reset_index(drop=True)
