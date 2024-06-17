# -*- coding = utf-8 -*-
# @Time: 2024-05-04 16:52:49
# @Author: Donvink wuwukai
# @Site: 
# @File: w_test.py
# @Software: PyCharm
import os
import json

from tqdm import tqdm
import pandas as pd
from websockets.protocol import Side

from common.json_encode import ComplexEncoder
from common.log import logger
from common.tools import record_time
from config.settings import BASE_DIR
from exceptions.custom_exceptions import TestEndingError
from order import OrderKindEnum
from order.enums import SideEnum
from src.strategy.devour_form import DevourFormStrategy


class TestDevourStrategy(DevourFormStrategy):

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
                res = [i.dict() for i in self.backtest_info.order_list]
                df = pd.DataFrame(res)
                buy = df.loc[df.side == SideEnum.BUY]
                sell = df.loc[df.side == SideEnum.SELL]
                buy['profit'] = (buy.close_price - buy.open_price) / buy.open_price
                sell['profit'] = (sell.open_price - sell.close_price) / sell.open_price
                total = pd.concat([buy, sell])
                total.to_pickle(f"{self.symbol}-{self.__class__.__name__}.pkl")
                logger.info(f"回测结束")
                return
            except Exception as e:
                logger.exception(f"执行异常")
                raise e


if __name__ == '__main__':
    TestDevourStrategy(symbol="ETHUSDT",
                  interval='1h',
                  backtest=True,
                  order_kind=OrderKindEnum.BINANCE,
                  backtest_path=os.path.join(os.path.dirname(BASE_DIR), 'test_data', 'ETHUSDT_FUTURES_回测1h.pkl'),
                  backtest_future_path=os.path.join(os.path.dirname(BASE_DIR), 'test_data', 'ETHUSDT_FUTURES_回测1h.pkl')
                  ).execute()
