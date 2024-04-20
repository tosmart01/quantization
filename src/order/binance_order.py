# -*- coding = utf-8 -*-
# @Time: 2024-04-07 16:52:30
# @Author: Donvink wuwukai
# @Site: 
# @File: BinanceOrder.py
# @Software: PyCharm
import pandas as pd

from common.decorator import error_email_notify
from common.log import logger
from common.tools import series_to_dict
from config.settings import RECEIVE_EMAIL
from models.order import Order
from notices.email_notify import send_trade_email
from order.enums import SideEnum, DirectionEnum
from order.market import market
from .order_mixin import OrderMixin

from schema.order_schema import OrderModel
from schema.backtest import Backtest
from .tools import get_stop_loss_price


class BinanceOrder(OrderMixin):

    @error_email_notify(name="查询余额失败")
    def get_all_money(self) -> float:
        money = market.get_money()
        return round(money['available_money'], 2)

    @error_email_notify(name="查询订单失败")
    def get_open_order(self, symbol: str, backtest: Backtest) -> OrderModel:
        if backtest.open_back:
            return self.get_open_fake_order(symbol, backtest)
        binance_order = market.get_open_order(symbol=symbol)
        db_order = Order.objects.get_order_by_symbol(symbol=symbol)
        if binance_order or db_order:
            return db_order.to_schema()

    @error_email_notify(name="创建订单失败")
    def create_order(self, symbol: str, backtest: Backtest, df: pd.DataFrame, interval: str = '5m',
                     compare_k: pd.Series = None, side: SideEnum = None, usdt: float = None,
                     leverage: int = 5) -> OrderModel:
        if backtest.open_back:
            return self.create_fake_order(symbol, backtest, df, interval, compare_k, side, leverage=leverage)
        market.set_leverage(symbol, leverage)
        usdt = leverage * usdt
        order = market.create_order(symbol, side=side, usdt=usdt)
        open_price = float(market.get_open_order(symbol)['entryPrice'])
        k: pd.Series = df.iloc[-1]
        order_model = Order.objects.create(symbol=symbol,
                                           interval=interval,
                                           active=True,
                                           start_time=k.date,
                                           start_data=series_to_dict(k),
                                           compare_data=series_to_dict(compare_k),
                                           side=side.value,
                                           leverage=leverage,
                                           open_price=open_price)
        order_schema: OrderModel = order_model.to_schema()
        stop_price = get_stop_loss_price(order_schema, k, df)
        from strategy.tools import get_low_point
        low_point = get_low_point(df, order_schema)
        message = f"下单成功,{symbol=}, usdt={usdt / leverage:.2f}, {leverage=}, db_id={order_model.id}, {order=}"
        logger.info(message)
        self.create_stop_loss(order_schema, stop_price)
        Order.objects.update_obj(order_model, properties={"low_point": series_to_dict(low_point), "stop_price": stop_price})
        send_trade_email(subject=f"下单成功,{symbol=}, usdt={usdt / leverage:.2f}", content=message,
                         to_recipients=RECEIVE_EMAIL)
        return order

    @error_email_notify(name="创建止损失败")
    def create_stop_loss(self, order: OrderModel, stop_price: float):
        order_info = market.create_stop_order(symbol=order.symbol, side=order.side.negation(), stop_price=stop_price)
        logger.info(f"{order.symbol=}止损设置成功, {order_info=}")

    @error_email_notify(name="平仓失败")
    def close_order(self, backtest: Backtest, order: OrderModel, df: pd):
        if backtest.open_back:
            return self.close_fake_order(order, df)
        close_info = market.close_position(symbol=order.symbol, side=order.side.negation())
        cancel_info = market.cancel_stop_order(symbol=order.symbol)
        k = df.iloc[-1]
        update_info = Order.objects.update_by_id(order.db_id, properties={"active": False,
                                                                          "end_data": series_to_dict(k),
                                                                          "close_price": k.close,
                                                                          "end_time": k.date.to_pydatetime()})
        profit = (order.open_price - k.close) / k.close
        message = f"symbol={order.symbol} 平仓成功, 预期获利={profit:.3%}, update_info={update_info}, {close_info=}, {cancel_info=}"
        logger.info(message)
        send_trade_email(subject=f"symbol={order.symbol},平仓成功", content=message, to_recipients=RECEIVE_EMAIL)

    @error_email_notify(name="检查止损失败")
    def check_stop_loss(self, order: OrderModel, df: pd.DataFrame, direction: DirectionEnum,
                        backtest: Backtest) -> bool:
        if backtest.open_back:
            return self.fake_stop_loss(order, df, direction, backtest)
        stop_order = market.get_stop_order(symbol=order.symbol)
        if stop_order:
            return False
        else:
            k = df.iloc[-1]
            Order.objects.update_by_id(order.db_id, properties={"active": False, "close_price": order.compare_data.high,
                                                                "end_time": k.date.to_pydatetime(), "stop_loss": True,
                                                                "end_data": series_to_dict(order.compare_data)})
            logger.info(f"symbol={order.symbol},触发止损")
            send_trade_email(subject=f"symbol={order.symbol},触发止损", content="触发止损", to_recipients=RECEIVE_EMAIL)
            return True
