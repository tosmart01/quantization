# -*- coding = utf-8 -*-
# @Time: 2024-04-05 15:30:49
# @Author: Donvink wuwukai
# @Site: 
# @File: order_mixin.py
# @Software: PyCharm

from order.base_order import BaseOrder
from order.fake_order import FakeOrder


class OrderMixin(FakeOrder, BaseOrder):
    pass
