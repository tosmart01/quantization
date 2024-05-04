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
    left_bottom = Column(JSON, nullable=True, comment='left_bottom')
    right_bottom = Column(JSON, nullable=True, comment='right_bottom')
    head_point = Column(JSON, nullable=True, comment='head_point')
    last_high_data = Column(JSON, nullable=True, comment='last_high_data')
    usdt = Column(Float, nullable=True, comment='开仓金额')

    def to_schema(self):
        from schema.order_schema import OrderModel, OrderDataDict
        order_data_fields = [('start_data', self.start_data), ('end_data', self.end_data),
                             ('last_high_data', self.last_high_data),
                             ('compare_data', self.compare_data), ('low_point', self.low_point),
                             ('head_point', self.head_point), ('left_bottom', self.left_bottom),
                             ('right_bottom', self.right_bottom)]
        schema = OrderModel(symbol=self.symbol, active=self.active,
                            start_time=self.start_time, interval=self.interval,
                            close_price=self.close_price, open_price=self.open_price,
                            end_time=self.end_time,
                            db_id=self.id,
                            stop_loss=self.stop_loss, side=self.side, leverage=self.leverage,
                            stop_price=self.stop_price,
                            **{name: OrderDataDict(**value) for name, value in order_data_fields if value}
                            )
        return schema


Base.metadata.create_all(engine, )
