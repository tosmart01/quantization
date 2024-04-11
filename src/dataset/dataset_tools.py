# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:58:04
# @Author: Donvink wuwukai
# @Site: 
# @File: dataset.py
# @Software: PyCharm
import os
import pandas as pd
from retry import retry

from schema.backtest import Backtest
from config.settings import BACKTEST_DATA_DIR, TRADE_MAX_INTERVAL
from client.binance_client import client
from common.tools import format_df
from exceptions.custom_exceptions import TestEndingError, DataDeficiencyError


class DataModule:

    @retry(tries=3, delay=3)
    def fetch(self, symbol, interval, limit) -> list[list]:
        data = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        return data

    def get_klines(self, symbol: str, interval: str = '5m', limit: int = 500,
                   backtest_info: Backtest = None) -> pd.DataFrame:

        if backtest_info.open_back:
            return self.get_fake_klines(backtest_info)
        data = self.fetch(symbol, interval, limit)
        df = format_df(data, symbol)
        return df

    def get_fake_klines(self, backtest_info: Backtest) -> pd.DataFrame:
        df = backtest_info.df.loc[backtest_info.start_offset: backtest_info.end_offset].reset_index(drop=True)
        if df.empty or backtest_info.end_offset > len(backtest_info.df):
            raise TestEndingError()
        if backtest_info.end_offset - backtest_info.start_offset < TRADE_MAX_INTERVAL:
            backtest_info.end_offset += 1
        else:
            backtest_info.start_offset += 1
            backtest_info.end_offset += 1
        return df

    def load_fake_klines(self, symbol: str) -> pd.DataFrame:
        file_list = os.listdir(BACKTEST_DATA_DIR)
        for path in file_list:
            if symbol.lower() in path.lower():
                df = pd.read_pickle(os.path.join(BACKTEST_DATA_DIR, path))
                df['tr'] = df['high'] - df['low']
                df['is_bull'] = df['close'] > df['open']
                return df.loc[(df['date'] >= '2024-02-10 00:00:00') & (df['date'] < '2024-02-18 00:30:00')
                       ].reset_index(drop=True)
                # return df.reset_index(drop=True)
        raise DataDeficiencyError()
