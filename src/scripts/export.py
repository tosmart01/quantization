# -*- coding = utf-8 -*-
# @Time: 2024-04-24 20:35:17
# @Author: Donvink wuwukai
# @Site: 
# @File: export.py
# @Software: PyCharm
import re
import os.path
from datetime import timedelta, datetime

import pandas as pd
from binance.enums import HistoricalKlinesType

from client.binance_client import client
from common.tools import format_df
from config.settings import BASE_DIR


def export(symbol, start_date: str, end_date: str, type=HistoricalKlinesType.FUTURES, interval='1h'):
    res = []
    length = 1000
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    start_date, end_date = start_date - timedelta(hours=8), end_date - timedelta(hours=8)
    period, pd_interval = re.search('(\d+)(\w+)', interval).groups()
    period_map = {
        'm': pd.offsets.Minute,
        'h': pd.offsets.Hour,
        'd': pd.offsets.Day,
        'w': pd.offsets.Week,
        'y': pd.offsets.YearEnd
    }
    date_range: list[datetime] = list(pd.date_range(start_date, end_date, freq=period_map[pd_interval](int(period))))
    for date in date_range[::1000]:
        index = date_range.index(date)
        start = date.strftime('%Y-%m-%d %H:%M:%S')
        if index + length < len(date_range):
            end = date_range[index + length - 1].strftime('%Y-%m-%d %H:%M:%S')
        else:
            end = date_range[-1].strftime('%Y-%m-%d %H:%M:%S')
        data = client.get_historical_klines(symbol=symbol, interval=interval, limit=length,
                                            start_str=start,
                                            end_str=end, klines_type=type
                                            )
        df = format_df(data, symbol, add_field=False)
        res.append(df)
        if index + length >= len(date_range):
            break
    total = pd.concat(res)
    total = total.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    return total

if __name__ == '__main__':
    symbol = 'BTCUSDT'
    interval = '4h'
    for _type in [HistoricalKlinesType.FUTURES, HistoricalKlinesType.SPOT]:
        df = export(symbol=symbol, start_date='2021-01-01', end_date='2024-05-30', interval=interval, type=_type)
        save_path = os.path.join(os.path.dirname(BASE_DIR), 'test_data', f'{symbol}_{_type.name}_回测{interval}.pkl')
        df.to_pickle(save_path)
        print(df.shape, _type)
    # df.to_pickle(f"/path/symbol.pkl")
