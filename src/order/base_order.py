# -*- coding = utf-8 -*-
# @Time: 2024-04-04 21:02:24
# @Author: Donvink wuwukai
# @Site: 
# @File: order.py
# @Software: PyCharm
from abc import ABC, abstractmethod


class BaseOrder(ABC):
    @abstractmethod
    def get_open_order(self, *args, **kwargs):
        ...

    @abstractmethod
    def create_order(self, *args, **kwargs):
        ...

    @abstractmethod
    def create_stop_loss(self, *args, **kwargs):
        ...

    @abstractmethod
    def close_order(self, *args, **kwargs):
        ...

    @abstractmethod
    def check_stop_loss(self, *args, **kwargs):
        ...
