# -*- coding = utf-8 -*-
# @Time: 2024-06-01 16:12:42
# @Author: Donvink wuwukai
# @Site: 
# @File: nr_test.py
# @Software: PyCharm
import json
import os

import pandas as pd
from tqdm import tqdm

from common.json_encode import ComplexEncoder
from common.log import logger
from common.tools import record_time
from exceptions.custom_exceptions import TestEndingError
from order.enums import OrderKindEnum
from schema.order_schema import OrderModel
from strategy.nr4 import NrStrategy
from config.settings import BASE_DIR


class NRTestStrategy(NrStrategy):

    @record_time
    def execute(self, *args, **kwargs):
        if self.backtest_info.open_back:
            self.t = tqdm(range(self.backtest_info.end_offset, self.backtest_info.df.__len__()))
        while True:
            try:
                order = self.order_module.get_open_order(self.symbol, self.backtest_info)
                if order:
                    self.exit_signal(order)
                else:
                    self.entry_signal()
            except TestEndingError:
                df = pd.DataFrame([i.dict() for i in self.backtest_info.order_list])
                df.loc[df.side == 'BUY', 'profit'] = (df.loc[df.side == 'BUY', 'close_price'] - df.loc[df.side == 'BUY', 'open_price']) /  df.loc[df.side == 'BUY', 'open_price']
                df.loc[df.side == 'SELL', 'profit'] = (df.loc[df.side == 'SELL', 'open_price'] - df.loc[df.side == 'SELL', 'close_price']) /  df.loc[df.side == 'SELL', 'open_price']
                df['side'] = df['side'].apply(lambda x: x.name)
                df.to_csv(f"nr_test_{self.interval}.csv")
                logger.info(f"回测结束")
                return
            except Exception as e:
                logger.exception(f"执行异常")
                raise e


if __name__ == '__main__':
    NRTestStrategy(symbol="BTCUSDT",
                  interval='15m',
                  backtest=True,
                  order_kind=OrderKindEnum.BINANCE,
                  backtest_path=os.path.join(os.path.dirname(BASE_DIR), 'test_data', 'BTCUSDT_FUTURES_回测15m.pkl'),
                  backtest_future_path=os.path.join(os.path.dirname(BASE_DIR), 'test_data', 'BTCUSDT_FUTURES_回测15m.pkl'),
                  ).execute()

