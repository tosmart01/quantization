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

from common.json_encode import ComplexEncoder
from common.log import logger
from common.tools import record_time
from config.settings import BASE_DIR
from exceptions.custom_exceptions import TestEndingError, StrategyNotMatchError
from order import OrderKindEnum
from src.strategy.w_bottom import WBottomStrategy


class TestWBottomStrategy(WBottomStrategy):

    def entry_signal(self):
        ### 测试使用 =========
        # test_dates = [
        #     pd.to_datetime('2024-05-08 08:00:00')
        # ]
        # df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        # if df.iloc[-1]['date'] not in test_dates:
        #     return
        ### ============
        self.t.update(1)
        df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        try:
            order_schema = self.find_w_bottom_entry(df)
        except StrategyNotMatchError:
            order_schema = None
        if order_schema:
            logger.info(f"条件单出现, symbol={self.symbol}, 日期={df.iloc[-1]['date']}")
            order = self.order_module.create_order(backtest=self.backtest_info,
                                                   df=df,
                                                   usdt=self.buy_usdt,
                                                   order_schema=order_schema
                                                   )
            return order

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
                json.dump([i.dict() for i in self.backtest_info.order_list], open(f'{self.symbol}_backdump.json', 'w'),
                          ensure_ascii=False, cls=ComplexEncoder)
                logger.info(f"回测结束")
                return
            except Exception as e:
                logger.exception(f"执行异常")
                raise e


if __name__ == '__main__':
    TestWBottomStrategy(symbol="BTCUSDT",
                  interval='15m',
                  backtest=True,
                  order_kind=OrderKindEnum.BINANCE,
                  backtest_path=os.path.join(os.path.dirname(BASE_DIR), 'test_data', 'BTCUSDT_SPOT_回测1h.pkl'),
                  backtest_future_path=os.path.join(os.path.dirname(BASE_DIR), 'test_data', 'BTCUSDT_FUTURES_回测1h.pkl')
                  ).execute()
