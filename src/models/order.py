# -*- coding = utf-8 -*-
# @Time: 2024-03-23 15:47:12
# @Author: Donvink wuwukai
# @Site: 
# @File: model.py
# @Software: PyCharm
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, SmallInteger

from controller.order import OrderController
from models.base import BaseModel, Base, engine
from schema.order_schema import OrderModel, OrderDataDict


class Order(BaseModel):
    __tablename__ = 'order'
    objects = OrderController()

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32), index=True, comment="标的代码")
    interval = Column(String(8), comment='下单周期')
    active = Column(Boolean, comment="是否打开")
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime, index=True, nullable=True)
    start_data = Column(JSON, comment="开仓k线数据", nullable=True, default={})
    end_data = Column(JSON, comment="平仓k线数据", nullable=True, default={})
    compare_data = Column(JSON, comment="开仓对比k线的数据", nullable=True, default={})
    open_price = Column(Float, comment='开仓价格')
    close_price = Column(Float, comment="平仓价格", nullable=True)
    stop_price = Column(Float, comment='止损价格', nullable=True)
    stop_loss = Column(Boolean, nullable=True, comment="是否触发限价停损", default=False)
    create_time = Column(DateTime, default=datetime.datetime.now, index=True)
    update_time = Column(DateTime, default=datetime.datetime.now, index=True)
    side = Column(String(16), nullable=True, comment='开仓方向')
    leverage = Column(SmallInteger, nullable=True, comment="杠杆")
    low_point = Column(JSON, nullable=True, comment='平仓参考低点')

    def to_schema(self) -> OrderModel:
        schema = OrderModel(symbol=self.symbol, active=self.active,
                   start_time=self.start_time, interval=self.interval,
                   end_time=self.end_time, start_data=OrderDataDict(**self.start_data),
                   end_data=OrderDataDict(**self.end_data) if self.end_data else None,
                   compare_data=OrderDataDict(**self.compare_data) if self.compare_data else None,
                   close_price=self.close_price, open_price=self.open_price,
                   stop_loss=self.stop_loss, side=self.side, leverage=self.leverage,
                   db_id=self.id, low_point=OrderDataDict(**self.low_point) if self.low_point else None,
                   stop_price=self.stop_price
                   )
        return schema


Base.metadata.create_all(engine, )
