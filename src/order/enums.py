# -*- coding = utf-8 -*-
# @Time: 2024-04-05 16:44:51
# @Author: Donvink wuwukai
# @Site: 
# @File: enums.py
# @Software: PyCharm
from strenum import StrEnum
from enum import auto


class SideEnum(StrEnum):
    SELL = auto()
    BUY = auto()

    def negation(self):
        if self == SideEnum.SELL:
            return SideEnum.BUY
        if self == SideEnum.BUY:
            return SideEnum.SELL


class DirectionEnum(StrEnum):
    SHORT = auto()
    LONG = auto()


class OrderKindEnum(StrEnum):
    BINANCE = auto()
    FUTURE = auto()
    STOCK = auto()

