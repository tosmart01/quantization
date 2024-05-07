# -*- coding = utf-8 -*-
# @Time: 2024-04-25 22:49:28
# @Author: Donvink wuwukai
# @Site: 
# @File: order_config.py
# @Software: PyCharm
import os
import os.path
import inspect
import json

from config.settings import BASE_DIR
from common.log import logger


class Config:
    def __init__(self, config_path: str = None):
        self.json_path = config_path or os.path.join(BASE_DIR, 'order_info.json')
        self.last_change_time = None
        self.config_dict = None

    def load_json(self):
        with open(self.json_path, encoding='utf-8') as fp:
            data = json.load(fp)
            return data

    def get_key(self, symbol, key):
        change_time = os.path.getmtime(self.json_path)
        if not self.last_change_time:
            self.last_change_time = change_time
            self.config_dict = self.load_json()
            return self.config_dict[symbol][key]
        if self.last_change_time != change_time:
            self.last_change_time = change_time
            self.config_dict = self.load_json()
            logger.info(f"订单配置热重载, config={self.config_dict}")
            return self.config_dict[symbol][key]
        else:
            return self.config_dict[symbol][key]

    def buy_usdt(self, symbol: str):
        return self.get_key(symbol, 'buy_usdt')

    def leverage(self, symbol: str):
        return self.get_key(symbol, 'leverage')


order_config = Config()

