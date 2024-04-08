# -- coding: utf-8 --
# @Time : 2023/12/12 16:37
# @Author : zhuo.wang
# @File : buy_info.py
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel
import pandas as pd


class OrderEnums(Enum):
    OPEN = 1
    CLOSE = 0


class WinLossInfo(BaseModel):
    eq_number: float
    operator_type: str
    name: str


class BuyInfo(BaseModel):
    symbol: str
    side: str
    leverage: int
    u: int


class InfoModel(BaseModel):
    win_info: WinLossInfo = None
    loss_info: WinLossInfo = None
    buy_info: List[BuyInfo]
    first_num: float
    category: OrderEnums = OrderEnums.OPEN
    max_hour: int = None
    buy_date: str = None

    @property
    def eta(self):
        if self.buy_date:
            hours = (datetime.now() - pd.to_datetime(self.buy_date)).total_seconds() / 3600
            return self.max_hour - hours

class OrderModel(BaseModel):
    buy_list: List[InfoModel]
