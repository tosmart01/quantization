# -*- coding = utf-8 -*-
# @Time: 2024-03-23 16:09:49
# @Author: Donvink wuwukai
# @Site: 
# @File: src.py
# @Software: PyCharm


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta, sessionmaker
from sqlalchemy import create_engine, Column, Boolean
from controller.base import BaseController

from config.settings import DB_URL


class CustomDeclarativeMeta(DeclarativeMeta):

    def __init__(self, *args, **kwargs):
        super(CustomDeclarativeMeta, self).__init__(*args, **kwargs)
        if hasattr(self, 'objects'):
            self.objects.model_cls = self
            self.objects.base_filter = (self.objects.model_cls.is_delete == 0,)
            self.objects.session = session


Base = declarative_base(metaclass=CustomDeclarativeMeta)
engine = create_engine(DB_URL, echo=False, pool_size=10, pool_timeout=60)
Session = sessionmaker(bind=engine)
session = Session()


class BaseModel(Base):
    """基类表模板"""

    __abstract__ = True
    objects = BaseController()
    is_delete = Column(Boolean, nullable=False, default=False, comment="是否已删除")
    def to_dict(self, keys=None):
        if keys:
            return {c: getattr(self, c, None) for c in keys}
        else:
            return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
