# -*- coding = utf-8 -*-
# @Time: 2024-04-04 21:21:49
# @Author: Donvink wuwukai
# @Site: 
# @File: backtest.py
# @Software: PyCharm
from typing import Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict

from .order_schema import OrderModel


class Backtest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    symbol: str
    df: pd.DataFrame = None
    open_back: bool = False
    start_offset: int = None
    end_offset: int = None
    order_list: list[OrderModel] = []
    future_df: Optional[pd.DataFrame] = None


    def flush_k(self):
        self.start_offset += 1
        self.end_offset += 1