# -- coding: utf-8 --
# @Time : 2023/12/12 18:08
# @Author : pinbar
# @File : main.py
import click
from apscheduler.schedulers.background import BlockingScheduler

from config.settings import CRON_INTERVAL
from strategy import strategy_factory
from order.enums import OrderKindEnum
from heartbeat.beat import heartbeat

symbol_list = [
    'XRPUSDT',
    'BTCUSDT',
    'BNBUSDT',
    'BCHUSDT',
    'RSRUSDT',
    'LUNCUSDT',
    'STGUSDT',
    'ETHUSDT',
    'EOSUSDT',
    'ADAUSDT',
    'RVNUSDT',
    'ETCUSDT',
    'DOGEUSDT',
]


@click.command()
@click.option('--strategy', type=click.Choice(['m_head', 'w_bottom']),
              help='策略选择，目前可选, m_head(M头),w_bottom(w底部)', required=True)
@click.option('--symbol', type=click.STRING, help=f'币种选择，可选:{", ".join(symbol_list)}', required=True)
@click.option('--interval', type=click.STRING, help='时间周期, 5m, 15m, 30m, 1h', default='1h')
def command(strategy: str = None, interval: str = '1h', symbol: str = 'ETHUSDT', ):
    strategy_model = strategy_factory(name=strategy)
    scheduler = BlockingScheduler()
    model_instance = strategy_model(symbol=symbol,
                                    interval=interval,
                                    backtest=False,
                                    order_kind=OrderKindEnum.BINANCE,
                                    )
    scheduler.add_job(model_instance.execute, 'cron', hour='*', name=f"{symbol}-{strategy}",
                      minute=CRON_INTERVAL[interval], second='40',
                      )
    scheduler.add_job(heartbeat, 'cron', args=(strategy,), hour='*', name=f"{symbol}-{strategy}心跳检测",
                      minute='11',second='40')
    scheduler.start()


if __name__ == '__main__':
    command()
