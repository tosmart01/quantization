# -*- coding = utf-8 -*-
# @Time: 2024-04-04 20:23:43
# @Author: Donvink wuwukai
# @Site: 
# @File: __init__.py.py
# @Software: PyCharm
import warnings
warnings.filterwarnings("ignore")
from strategy.m_head import MHeadStrategy, BaseStrategy
from exceptions.custom_exceptions import UnsupportedStrategyError


def strategy_factory(name: str) -> BaseStrategy.__class__:
    if name == 'm_head':
        return MHeadStrategy
    else:
        raise UnsupportedStrategyError(add_error_message="M策略")
