# -*- coding = utf-8 -*-
# @Time: 2024-04-24 20:35:17
# @Author: Donvink wuwukai
# @Site: 
# @File: export.py
# @Software: PyCharm
import os.path
from datetime import timedelta

import pandas as pd
from binance.enums import HistoricalKlinesType

from client.binance_client import client
from common.tools import format_df
from config.settings import BASE_DIR


def export(symbol, start_date: str, end_date: str, type = HistoricalKlinesType.FUTURES, interval='1h'):
    res = []
    freq_map = {
        '1h': 1000
    }
    date_range = pd.date_range(start_date, end_date, freq=f"{freq_map[interval]}h")
    for date in date_range:
        start = (date - timedelta(hours=8)).strftime('%Y-%m-%d')
        end = (date + timedelta(hours=freq_map[interval]) - timedelta(hours=8)).strftime('%Y-%m-%d')
        data = client.get_historical_klines(symbol=symbol, interval=interval, limit=1000,
                         start_str=start,
                         end_str=end, klines_type=type
                         )
        df = format_df(data, symbol)
        res.append(df)
    total = pd.concat(res)
    total = total.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    return total


if __name__ == '__main__':
    symbol = 'ETHUSDT'
    interval = '1h'
    for _type in [HistoricalKlinesType.FUTURES, HistoricalKlinesType.SPOT]:
        df = export(symbol=symbol, start_date='2021-01-01', end_date='2024-05-09', interval=interval, type=_type)
        save_path = os.path.join(os.path.dirname(BASE_DIR), 'test_data', f'{symbol}_{_type.name}_回测{interval}.pkl')
        df.to_pickle(save_path)
        print(df.shape, _type)
    # df.to_pickle(f"/path/symbol.pkl")
