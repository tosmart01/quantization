import os
import sys

import pytz
from dotenv import load_dotenv

load_dotenv()

# BASE_DIR
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将BASE_DIR 假如搜索路径
sys.path.insert(0, BASE_DIR)
# [BASE]
ENV = os.getenv("ENV", "dev")
TZ = pytz.timezone(os.getenv("TZ", "Asia/Shanghai"))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, 'log'))
PROJECT_NAME = os.getenv("PROJECT_NAME", '')
BINANCE_KEY = os.getenv("BINANCE_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")

PROXIES = {
    'http': 'http://127.0.0.1:7078',
    'https': 'http://127.0.0.1:7078',
}

# 回测数据目录
BACKTEST_DATA_DIR = os.getenv("BACKTEST_DATA_DIR", os.path.join(BASE_DIR, 'data', 'test'))
# 获取极值区间长度
MAX_VALUE_PERIOD = int(os.getenv("MAX_VALUE_PERIOD", 10))
# 获取极值区间长度
MIN_VALUE_PERIOD = int(os.getenv("MIN_VALUE_PERIOD", 15))
# 每次交易最大k线数量
TRADE_MAX_INTERVAL = int(os.getenv("TRADE_MAX_INTERVAL", 300))
# 开仓M头 头部到颈部跌幅
M_DECLINE_PERCENT = float(os.getenv("M_DECLINE_PERCENT", 0.01))
# 判断为远距离高点时间, 单位 分钟
DECLINE_HIGH_TIME = int(os.getenv("DECLINE_HIGH_TIME", 1440))


DB_URL = os.getenv("DB_URL", f"sqlite:///{os.path.join(BASE_DIR, 'data', 'trade.db')}")
# 是否测试
MODEL_TEST = False
RECEIVE_EMAIL = []
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_PORT = int(os.getenv('HOST', 587))
EMAIL_HOST = os.getenv("EMAIL_HOST")
CACHE_DIR = os.getenv("CACHE_DIR", os.path.join(BASE_DIR, 'data', 'cache'))
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

CRON_INTERVAL = {
    "15m": '14,29,44,59',
    "5m": '4,9,14,19,24,29,34,39,44,49,54,59'
}

try:
    if ENV.lower() != "prod":
        exec(f"from config.{ENV} import *")
except ModuleNotFoundError as e:
    print(f"custom settings load fail:{e}")
