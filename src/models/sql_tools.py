# -*- coding = utf-8 -*-
# @Time: 2024-03-23 16:15:55
# @Author: Donvink wuwukai
# @Site: 
# @File: sql_tools.py
# @Software: PyCharm
from sqlalchemy import desc
from sqlalchemy.orm.query import Query as BaseQuery


def query_col(query_obj):
    """查询字段并转换为[{data1}, {data2}...]
    只可在查询对象为字段时使用
    """
    return [dict(zip(v.keys(), v)) for v in query_obj.all()]


def query_col_first(query_obj):
    """取第一条数据"""
    data = query_obj.first()
    if data:
        return {k: v for k, v in zip(data.keys(), data)}
    return {}


def query_all_values(query_obj):
    """查询字段并转换为[[data1, data2.]]"""
    return [list(v) for v in query_obj.all()]


def query_order(query: BaseQuery, order_by: str = None, table=None):
    if order_by:
        order_list = order_by.split(",")
        for order in order_list:
            order_c, order_s = order.split(":")
            if table is not None:
                order_c = getattr(table, order_c)
            if order_s == "desc":
                query = query.order_by(desc(order_c))
            else:
                query = query.order_by(order_c)

    return query


def pagination(query: BaseQuery, page: int = None, per_page: int = None):
    """
    基于sqlalchemy.BaseQuery.paginate封装的分页器方法，兼容排序的处理
    如果page<1，则不执行分页方法，按照query_col方法获取结果
    返回数据内容和分页配置信息
    :param query: 查询对象
    :param page: 页数，从1开始
    :param per_page: 页容量，默认20
    :return: 数据对象和分页信息
    """
    pager_info = {}
    if page:
        paginate = query.paginate(page, per_page, error_out=False)  # 当分页错误时，返回空

        pager_info["page"] = page
        pager_info["per_page"] = per_page if per_page else 10
        pager_info["total"] = paginate.total
        pager_info["pages"] = paginate.pages
        r = [dict(zip(v.keys(), v)) for v in paginate.items]
    else:
        r = query_col(query)

    return r, pager_info
