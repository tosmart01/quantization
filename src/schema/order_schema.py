# -*- coding = utf-8 -*-
# @Time: 2024-04-05 15:54:45
# @Author: Donvink wuwukai
# @Site: 
# @File: order_schema.py
# @Software: PyCharm
from datetime import datetime
from typing import Any, Optional

import pandas as pd
from pandas import Timestamp
from pydantic import BaseModel, ConfigDict, model_validator

from common.tools import series_to_dict
from order.enums import SideEnum


class OrderDataDict(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: Optional[Timestamp]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    pct_change: Optional[float]
    symbol: str
    tr: Optional[float]

    @model_validator(mode="before")
    @classmethod
    def check_card_number_omitted(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "date" in data:
                if isinstance(data['date'], str):
                    data['date'] = pd.to_datetime(data['date'])
        return data


class OrderModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    symbol: str
    interval: str
    active: bool = True
    start_time: Timestamp | datetime
    end_time: Optional[Timestamp | datetime] = None
    close_price: Optional[float] = None
    open_price: float
    stop_loss: bool = False
    side: SideEnum
    leverage: int
    stop_price: Optional[float] = None
    db_id: Optional[int] = None
    start_data: OrderDataDict = None
    end_data: Optional[OrderDataDict] = None
    last_high_data: Optional[OrderDataDict] = None
    compare_data: Optional[OrderDataDict] = None
    low_point: Optional[OrderDataDict] = None
    head_point: Optional[OrderDataDict] = None
    left_bottom: Optional[OrderDataDict] = None
    right_bottom: Optional[OrderDataDict] = None
    tr_ratio: Optional[float] = None

    def __str__(self):
        return f"{self.symbol=},{self.active=},{self.start_time=},{self.end_time}"

    def get_order_data_list(self) -> dict[str, dict]:
        fields = [('start_data', self.start_data), ('end_data', self.end_data),
                  ('last_high_data', self.last_high_data),
                  ('compare_data', self.compare_data), ('low_point', self.low_point),
                  ('head_point', self.head_point), ('left_bottom', self.left_bottom),
                  ('right_bottom', self.right_bottom)]
        res = {}
        for name, value in fields:
            if value:
                res[name] = series_to_dict(value)
        return res

    def order_data_field_to_dict(self, field) -> dict:
        value = getattr(self, field)
        if value:
            return value.dict()

    def dict_to_order_field(self, item: dict) -> OrderDataDict:
        return OrderDataDict(**item)
