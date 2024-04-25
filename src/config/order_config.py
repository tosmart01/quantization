# -*- coding = utf-8 -*-
# @Time: 2024-04-25 22:49:28
# @Author: Donvink wuwukai
# @Site: 
# @File: order_config.py
# @Software: PyCharm
import os.path
import inspect
import json

from config.settings import BASE_DIR


class Config:

    def get_key_from_json(self):
        json_path = os.path.join(BASE_DIR, 'order_info.json')
        key = inspect.currentframe().f_back.f_code.co_name
        with open(json_path, encoding='utf-8') as fp:
            data = json.load(fp)
            return data[key]
    @property
    def buy_usdt(self):
        return self.get_key_from_json()

    @property
    def leverage(self):
        return self.get_key_from_json()


order_config = Config()
