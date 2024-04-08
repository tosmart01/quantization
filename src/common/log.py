import os
import sys
import logging
import re
import threading

from loguru import logger as flask_logger
from config.settings import LOG_DIR, PROJECT_NAME, MODEL_TEST

logger = flask_logger.bind(is_flask=True)


class InterceptHandler(logging.Handler):
    """
    删除日志颜色

    不同框架底层方法在写入日志时,有可能被loguru判断为带颜色的日志从而进入后续处理,导致写入错误.
    请务必保留此方法,避免日志写入导致错误.
    """

    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info, colors=False)
        ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")  # 删除自带的颜色
        logger_opt.log(record.levelname, ansi_escape.sub("", record.getMessage()))


class ProcessThreadIDFilter:
    def __call__(self, record):
        record["extra"]["process_id"] = os.getpid()
        record["extra"]["thread_id"] = threading.get_ident()
        return True


def register_logger():
    """注册日志到loguru，由loguru统一管理日志的格式、旋转、错误等"""
    # [定义日志路径]
    os.makedirs(LOG_DIR, exist_ok=True)
    prefix = f"{PROJECT_NAME}_" if PROJECT_NAME else ""
    # [标准日志写入loguru] 此配置可将各库写入原生logging的日志配置入loguru,例如Flask
    logging.basicConfig(handlers=[InterceptHandler(level="INFO")], level="INFO")
    # [loguru日志输出至控制台] 对调试有帮助
    logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

    # 日志旋转、大小限制、更替等参数均支持多种配置,详情请参考文档
    # [logger参数文档: https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger]
    # 请务必设置colorize=False,避免在不同系统上由于颜色标签的写入造成问题
    logger.add(
        os.path.join(LOG_DIR , prefix , "info_{time:%Y-%m-%d}.log"),
        level="INFO",
        colorize=False,
        rotation="1 days",
        retention="7 days",
        backtrace=False,
        diagnose=False,
        encoding="utf-8",
        format="{time} {level} {message} | PID:{process} | TID: {thread}",
    )
    logger.add(
        os.path.join(LOG_DIR , prefix , "error_{time:%Y-%m-%d}.log"),
        level="ERROR",
        colorize=False,
        rotation="1 days",
        retention="15 days",
        backtrace=False,
        diagnose=False,
        encoding="utf-8",
        format="{time} {level} {message} | PID:{process} | TID: {thread}",
    )
    logger.add(
        os.path.join(LOG_DIR , prefix , "error_detail_{time:%Y-%m-%d}.log"),
        level="ERROR",
        colorize=False,
        rotation="1 days",
        retention="3 days",
        backtrace=True,
        diagnose=True,
        encoding="utf-8",
        format="{time} {level} {message} | PID:{process} | TID: {thread}",
    )

register_logger()
