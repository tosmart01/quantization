# -*- coding = utf-8 -*-
# @Time: 2024-04-05 17:30:56
# @Author: Donvink wuwukai
# @Site: 
# @File: json_encode.py
# @Software: PyCharm
import json
from pandas import Timestamp
from datetime import datetime


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Timestamp, datetime)):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return super().default(obj)
