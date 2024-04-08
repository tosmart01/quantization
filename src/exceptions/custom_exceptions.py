# -*- coding = utf-8 -*-
# @Time: 2024-04-04 21:27:55
# @Author: Donvink wuwukai
# @Site: 
# @File: custom_exceptions.py
# @Software: PyCharm
from exceptions.base import BaseException


class DataDeficiencyError(BaseException):
    default_error_message = "回测数据为空，请检查回测目录"


class TestEndingError(BaseException):
    default_error_code = "回测结束"


class UnsupportedOrderTypeError(BaseException):
    default_error_message = "不支持的订单类型, %s"


class UnsupportedStrategyError(BaseException):
    default_error_message = "不支持的策略,当前仅支持: %s"


class DateTimeError(BaseException):
    default_error_message = "执行时间异常"