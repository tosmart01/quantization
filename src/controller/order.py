# -*- coding = utf-8 -*-
# @Time: 2024-04-07 20:18:23
# @Author: Donvink wuwukai
# @Site: 
# @File: order.py
# @Software: PyCharm
from typing import TYPE_CHECKING

from controller.base import BaseController

if TYPE_CHECKING:
    from models.order import Order


class OrderController(BaseController):
    model_cls: "Order"

    def get_order_by_symbol(self, symbol: str) -> "Order":
        order = self.session.query(self.model_cls).filter(self.model_cls.symbol == symbol,
                                                  self.model_cls.active == True,
                                                  ).order_by(self.model_cls.create_time.desc()).first()
        return order
