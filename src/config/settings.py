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
# ============= M头配置
# 获取极值区间长度
MAX_VALUE_PERIOD = int(os.getenv("MAX_VALUE_PERIOD", 8))
# 获取极值区间长度
MIN_VALUE_PERIOD = int(os.getenv("MIN_VALUE_PERIOD", 8))
# 每次交易最大k线数量
TRADE_MAX_INTERVAL = int(os.getenv("TRADE_MAX_INTERVAL", 200))
# 开仓M头 头部到颈部跌幅比例
M_DECLINE_PERCENT = float(os.getenv("M_DECLINE_PERCENT", 2.7))
# 最小交易k线
MIN_TRADE_COUNT = int(os.getenv("MIN_TRADE_COUNT", 8))
# 最后一个高点到当前k线数量
NEAR_HIGH_K_COUNT = int(os.getenv("NEAR_HIGH_K_COUNT", 2))
# 对比前高的数量
COMPARE_HIGH_K_COUNT = int(os.getenv("COMPARE_HIGH_K_COUNT", 1))
# 设置止损最大比例
MAX_STOP_LOSS_RATIO = float(os.getenv("MAX_STOP_LOSS_RATIO", 0.4))
# 设置最大止损最大百分比（优先级最高）
MAX_STOP_LOSS_PERCENT = float(os.getenv("MAX_STOP_LOSS_PERCENT", 0.03))
# 判断布林带开口比例
OPENING_THRESHOLD = float(os.getenv("OPENING_THRESHOLD", 1.2))
# 判断布林带收敛比例
ASTRINGENCY_THRESHOLD = float(os.getenv("ASTRINGENCY_THRESHOLD", 0.8))
# 判断盘整区间末尾高点数量
CONSOLIDATION_HIGH_COUNT = int(os.getenv("CONSOLIDATION_HIGH_COUNT", 5))
# ===============================

# W底配置
NEAR_LOW_K_COUNT = int(os.getenv("NEAR_LOW_K_COUNT", 2))


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
    "1h": "59",
    "15m": '14,29,44,59',
    "5m": '4,9,14,19,24,29,34,39,44,49,54,59'
}

try:
    if ENV.lower() != "prod":
        exec(f"from config.{ENV} import *")
except ModuleNotFoundError as e:
    print(f"custom settings load fail:{e}")
