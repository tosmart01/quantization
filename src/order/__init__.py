# -- coding: utf-8 --
# @Time : 2023/12/12 18:05
# @Author : zhuo.wang
# @File : __init__.py.py
from order.binance_order import BinanceOrder
from order.enums import OrderKindEnum
from exceptions.custom_exceptions import UnsupportedOrderTypeError


def factory_order_model(name: str) -> BinanceOrder:
    if name == OrderKindEnum.BINANCE:
        return BinanceOrder()
    else:
        raise UnsupportedOrderTypeError(add_error_message="当前仅支持币安合约交易")
