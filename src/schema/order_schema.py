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
    end_time: Optional[Timestamp| datetime] = None
    start_data: OrderDataDict
    end_data: Optional[OrderDataDict] = None
    compare_data: OrderDataDict
    close_price: Optional[float] = None
    open_price: float
    stop_loss: bool = False
    side: SideEnum
    leverage: int
    db_id: Optional[int] = None
    low_point: Optional[OrderDataDict] = None
    stop_price: Optional[float] = None

    def __str__(self):
        return f"{self.symbol=},{self.active=},{self.start_time=},{self.end_time}"
