# -*- coding = utf-8 -*-
# @Time: 2024-04-24 20:35:17
# @Author: Donvink wuwukai
# @Site: 
# @File: export.py
# @Software: PyCharm

from glob import glob
from datetime import datetime
import pandas as pd

symbol_list = [
    'XRP/USDT',
    'BTC/USDT',
    'ATOM/USDT',
    'BCH/USDT',
    'RSR/USDT',
    'LUNC/USDT',
    'STG/USDT',
    'ETH/USDT',
    'EOS/USDT',
    'ADA/USDT',
    'RVN/USDT',
    'ETC/USDT',
    'DOGE/USDT',
]

def export(file_list):
    res = []
    for path in file_list:
        for symbol in symbol_list:
            if symbol.split('/')[0] in path:
                df = pd.read_csv(path,header=None)
                if df.iloc[0,0] == 'open_time':
                    df = df.iloc[1:,::]
                    for i in range(5):
                        df[i] = df[i].astype(float)
                df[0] = df[0].apply(lambda x:datetime.fromtimestamp(x/1000))
                df = df.iloc[::,:6]
                df.columns = ['date','open','high','low','close','volume']
                df['pct_change'] = df['close'].pct_change() * 100
                df['symbol'] = symbol
                res.append(df)

    total = pd.concat(res)
    return total


if __name__ == '__main__':
    file_list = glob(r'/path/*.csv')
    df = export(file_list)
    print(df)
    # df.to_pickle(f"/path/symbol.pkl")
