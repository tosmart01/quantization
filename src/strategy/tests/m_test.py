# -*- coding = utf-8 -*-
# @Time: 2024-04-07 23:22:47
# @Author: Donvink wuwukai
# @Site: 
# @File: m_test.py
# @Software: PyCharm
import json
import os

from tqdm import tqdm

from common.json_encode import ComplexEncoder
from common.log import logger
from common.tools import record_time
from exceptions.custom_exceptions import TestEndingError
from order.enums import OrderKindEnum
from schema.order_schema import OrderModel
from strategy.m_head import MHeadStrategy
from config.settings import BASE_DIR


class MTestStrategy(MHeadStrategy):

    def entry_signal(self) -> OrderModel:
        ### 测试使用 =========
        # test_dates = [
        #     pd.to_datetime('2022-01-27 12:00:00')
        # ]
        # df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        # if df.iloc[-1]['date'] not in test_dates:
        #     return
        ### ============
        if self.backtest_info.open_back:
            self.t.update(1)
        df = self.data_module.get_klines(self.symbol, interval=self.interval, backtest_info=self.backtest_info)
        order_schema = self.check_near_prior_high_point(df)
        if order_schema:
            logger.info(f"条件单出现, symbol={self.symbol}, 日期={df.iloc[-1]['date']}")
            order = self.order_module.create_order(backtest=self.backtest_info,
                                                   df=df,
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
    MTestStrategy(symbol="ETHUSDT",
                  interval='1h',
                  backtest=True,
                  order_kind=OrderKindEnum.BINANCE,
                  backtest_path=os.path.join(os.path.dirname(BASE_DIR), 'test_data', 'ETHUSDT_SPOT_回测1h.pkl')
                  ).execute()

