# -- coding: utf-8 --
# @Time : 2023/12/12 16:08
# @Author : pinbar
# @File : market.py
from retry import retry

from client.binance_client import client
from order.enums import SideEnum


class MarketEngine:
    symbol_list = client.futures_exchange_info()['symbols']
    marginType = "ISOLATED"

    def get_new_price(self, symbol=None):
        price = client.futures_mark_price(symbol=symbol)
        return float(price["markPrice"])

    @retry(tries=3, delay=0.5)
    def get_money(self):
        """
        totalMarginBalance 总资产
        availableBalance 可用保证金
        :return:
        """
        data = client.futures_account()
        return {
            "all_money": float(data["totalMarginBalance"]),
            "available_money": float(data["availableBalance"]),
        }

    def set_leverage(
            self,
            symbol,
            leverage=5
    ):
        """设置杠杆
        """
        try:
            res = client.futures_change_margin_type(
                symbol=symbol, marginType=self.marginType
            )
        except Exception as e:
            pass
        try:
            leverage = client.futures_change_leverage(
                symbol=symbol, leverage=leverage
            )
        except Exception as e:
            leverage = client.futures_change_leverage(
                symbol=symbol, leverage=5
            )

    def get_precision(self, symbol: str):
        '''查询下单精度
        '''
        for i in self.symbol_list:
            if i['symbol'] == symbol:
                return i['quantityPrecision']

    def get_quantity(self, symbol, usdt: float):
        ''' 查询usdt对应的下单币种数量，将usdt转为币种数量
        '''
        price = self.get_new_price(symbol)
        round_num = self.get_precision(symbol)
        return round(usdt / price, round_num)

    @retry(tries=3, delay=0.5)
    def get_open_order(self, symbol: str) -> dict:
        """
        返回当前仓位订单，不包括止盈止损
        @param symbol:
        @return:{'symbol': 'ETHUSDT',
                 'positionAmt': '0.007',
                 'entryPrice': '3388.0',
                 'breakEvenPrice': '3389.694',
                 'markPrice': '3388.00000000',
                 'unRealizedProfit': '0.00000000',
                 'liquidationPrice': '0',
                 'leverage': '2',
                 'maxNotionalValue': '500000000',
                 'marginType': 'cross',
                 'isolatedMargin': '0.00000000',
                 'isAutoAddMargin': 'false',
                 'positionSide': 'BOTH',
                 'notional': '23.71600000',
                 'isolatedWallet': '0',
                 'updateTime': 1712492152474,
                 'isolated': False,
                 'adlQuantile': 0}
        """
        orders = client.futures_position_information(symbol=symbol)
        for o in orders:
            if o['notional'] != "0":
                return o

    @retry(tries=3, delay=0.5)
    def get_stop_order(self, symbol: str) -> dict:
        """

        @param symbol:
        @return: {'orderId': 8389765669432904407,
             'symbol': 'ETHUSDT',
             'status': 'NEW',
             'clientOrderId': 'SK101rgiVCwcsyyUzDJW6E',
             'price': '0',
             'avgPrice': '0.00000',
             'origQty': '0',
             'executedQty': '0',
             'cumQuote': '0',
             'timeInForce': 'GTC',
             'type': 'STOP_MARKET',
             'reduceOnly': True,
             'closePosition': True,
             'side': 'SELL',
             'positionSide': 'BOTH',
             'stopPrice': '3000',
             'workingType': 'CONTRACT_PRICE',
             'priceMatch': 'NONE',
             'selfTradePreventionMode': 'NONE',
             'goodTillDate': 0,
             'priceProtect': False,
             'origType': 'STOP_MARKET',
             'time': 1712476287547,
             'updateTime': 1712476287547}
        """
        orders = client.futures_get_open_orders()
        for order in orders:
            if order['symbol'] == symbol and order['type'] == "STOP_MARKET":
                return order

    @retry(tries=3, delay=0.5)
    def close_position(self, symbol: str, side: SideEnum, quantity=None):
        """
        指定币种平仓
        @param symbol: 币种
        @param side: 方向
        @param quantity: 平仓金额，默认全部平仓
        @return:
        """
        base_quantity = self.get_open_order(symbol)['positionAmt']
        base_quantity = abs(float(base_quantity))
        if quantity is not None:
            # 如果当前配对币种有多个单子，则使用杠杆自动计算仓位平仓
            if quantity / base_quantity <= 0.85:
                base_quantity = quantity
        return client.futures_create_order(symbol=symbol,
                                                   side=side.value,
                                                   type="MARKET",
                                                   quantity=base_quantity)

    @retry(tries=3, delay=0.5)
    def create_order(self, symbol: str, side: SideEnum, usdt: float):
        """
        下单，这里是计算杠杆后的下单usdt数量，例如杠杆是10倍, 下单100U， 则这里需要传usdt=100*10
        @param symbol:
        @param side: 下单方向
        @param usdt: 计算杠杆后的下单usdt数量
        @return:
        """
        quantity = self.get_quantity(symbol, usdt)
        order = client.futures_create_order(symbol=symbol,
                                                    side=side.value,
                                                    type="MARKET",
                                                    quantity=quantity)
        return order


    @retry(tries=3, delay=0.5)
    def create_stop_order(self, symbol: str, stop_price: float, side: SideEnum):
        """
        创建市价停损单
        @param symbol: 币种代码
        @param stop_price: 停损价格
        @param side: 与当前仓位相反
        @return: {'orderId': 8389765669432904407,
                 'symbol': 'ETHUSDT',
                 'status': 'NEW',
                 'clientOrderId': 'SK101rgiVCwcsyyUzDJW6E',
                 'price': '0.00',
                 'avgPrice': '0.00',
                 'origQty': '0.000',
                 'executedQty': '0.000',
                 'cumQty': '0.000',
                 'cumQuote': '0.00000',
                 'timeInForce': 'GTC',
                 'type': 'STOP_MARKET',
                 'reduceOnly': True,
                 'closePosition': True,
                 'side': 'SELL',
                 'positionSide': 'BOTH',
                 'stopPrice': '3000.00',
                 'workingType': 'CONTRACT_PRICE',
                 'priceProtect': False,
                 'origType': 'STOP_MARKET',
                 'priceMatch': 'NONE',
                 'selfTradePreventionMode': 'NONE',
                 'goodTillDate': 0,
                 'updateTime': 1712476287547}
        """
        return client.futures_create_order(symbol=symbol,
                                    stopPrice=stop_price,
                                    type="STOP_MARKET",
                                    side=side.value,
                                    closePosition=True,
                                    )

    @retry(tries=3, delay=0.2)
    def cancel_stop_order(self, symbol: str):
        stop_order = self.get_stop_order(symbol=symbol)
        if stop_order:
            order_id = stop_order['orderId']
            return client.futures_cancel_order(symbol=symbol, orderid=order_id)


market = MarketEngine()