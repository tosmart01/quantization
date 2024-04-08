# -*- coding = utf-8 -*-
# @Time: 2024-03-23 16:19:01
# @Author: Donvink wuwukai
# @Site: 
# @File: src.py
# @Software: PyCharm
from itertools import chain
from typing import Union, List, Dict, Any

from sqlalchemy import desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import Table

from models.sql_tools import query_col, query_all_values


class BaseController:
    """
    Base BaseController, implement src CRUD sqlalchemy operations
    """

    model_cls:Table = None
    session: Session = None
    base_filter = ()

    def get_query(self, query_field):
        query = self.session.query(self.model_cls)
        if query_field:
            query = self.session.query(*query_field)
        return query

    def order_by(self, order=None, queryset=None):
        order_conditions = []
        if isinstance(order, str):
            order_conditions = (
                [desc(order.replace("-", ""))]
                if order.startswith("-")
                else [asc(order)]
            )
        if isinstance(order, (list, tuple)):
            order_conditions = [
                desc(i.replace("-", "")) if i.startswith("-") else asc(i) for i in order
            ]
        return queryset.order_by(*order_conditions)

    def get_by_id(
            self,
            model_id: Union[int, str],
            query_field: Union[List, tuple] = None,
            to_dict: bool = False,
            id_field: str = None,
    ) -> model_cls or None:
        """

        :param model_id: ID
        :param query_field: [User.username,User.id],返回指定字段
        :param to_dict: to_dict
        :param id_field:
        :return:
        """
        id_col = getattr(self.model_cls, id_field or "id", None)
        if not id_col:
            return None

        query = self.get_query(query_field)

        queryset = query.filter(id_col == model_id, *self.base_filter)
        obj = queryset.one_or_none()

        if to_dict and obj:
            return dict(zip(obj.keys(), obj)) if query_field else obj.to_dict()

        return obj

    def get_by_ids(
            self,
            model_ids: List,
            query_field=None,
            to_dict=False,
            order_by=None,
            values_list=False,
            id_field: str = None,
    ) -> List[model_cls]:
        """

        :param model_ids: ids
        :param query_field: 返回指定字段
        :param to_dict: False|True {'username':'test',...}
        :param order_by: list|tuple|str >
                        asc order_by = 'create_time',  order_by = ['create_time','id']
                        desc order_by = '-create_time' order_by = ['-create_time','-id']
        :param values_list: False|True 返回格式 [value1,value2]
        :param id_field:
        :return:
        """
        id_col = getattr(self.model_cls, id_field or "id", None)
        if id_col is None:
            return []

        query = self.get_query(query_field)
        queryset = query.filter(id_col.in_(model_ids), *self.base_filter)
        queryset = self.order_by(order=order_by, queryset=queryset)

        if to_dict:
            return (
                query_col(queryset)
                if query_field
                else [i.to_dict() for i in queryset.all()]
            )

        if values_list:
            return (
                list(chain(*queryset.all())) if query_field else query_all_values(query)
            )

        return queryset.all()

    def get_by_field(
            self,
            model_id: Union[int, str],
            field: str = None,
            to_dict=False,
            query_field=None,
    ):
        id_col = getattr(self.model_cls, field or "id", None)
        if not id_col:
            return None
        query = self.get_query(query_field)
        queryset = query.filter(id_col == model_id, *self.base_filter)
        if to_dict:
            return (
                query_col(queryset)
                if query_field
                else [i.to_dict() for i in queryset.all()]
            )
        return queryset.all()

    def get_by_fields(
            self, model_ids: List, field=None, query_field=None, to_dict=False, order_by=None
    ):
        id_col = getattr(self.model_cls, field or "id", None)
        if not id_col:
            return None
        query = self.get_query(query_field)
        queryset = query.filter(id_col.in_(model_ids), *self.base_filter)
        queryset = self.order_by(order=order_by, queryset=queryset)

        if to_dict:
            return (
                query_col(queryset)
                if query_field
                else [i.to_dict() for i in queryset.all()]
            )
        return queryset.all()

    def get_all(self, to_dict=False, query_field=None, order_by=None) -> List[model_cls]:
        """
        Get all that fit the `base_filter`
        """
        query = self.get_query(query_field)
        queryset = query.filter(*self.base_filter)
        if to_dict:
            return (
                query_col(queryset)
                if query_field
                else [i.to_dict() for i in queryset.all()]
            )

        queryset = self.order_by(order=order_by, queryset=queryset)
        return queryset.all()

    def create(
            self,
            commit: bool = True,
            **properties: Dict[str, Any],
    ) -> model_cls:
        """
        Generic for creating models
        :raises: DAOCreateFailedError
        """

        model = self.model_cls  # pylint: disable=not-callable
        obj = model(**properties)

        try:
            self.session.add(obj)
            self.session.flush()
            if commit:
                self.session.commit()
        except SQLAlchemyError as ex:  # pragma: no cover
            self.session.rollback()
            raise ex
        return obj

    def update(
            self,
            queryset,
            properties: Dict[str, Any] = None,
            is_commit=True,
    ):
        """
        filter对象批量更新
        :param queryset:
        :param properties:
        :param is_commit:
        :return:
        """
        try:
            modify_count = queryset.filter(*self.base_filter).update(
                properties, synchronize_session=False
            )
            if is_commit:
                self.session.commit()
        except SQLAlchemyError as ex:
            self.session.rollback()
            raise ex
        return modify_count

    def update_obj(
            self, model: model_cls, properties: Dict[str, Any], commit: bool = True
    ) -> model_cls:
        """
        Generic update a model
        :raises: DAOCreateFailedError
        """
        if not model:
            return model
        for key, value in properties.items():
            setattr(model, key, value)
        try:
            self.session.merge(model)
            if commit:
                self.session.commit()
        except SQLAlchemyError as ex:  # pragma: no cover
            self.session.rollback()
            raise ex
        return model

    def update_by_id(
            self,
            model_id: Union[int, str],
            properties: Dict[str, Any] = None,
            is_commit=True,
            id_field="id",
    ):
        query = self.session.query(self.model_cls)
        id_col = getattr(self.model_cls, id_field or "id", None)
        modify_count = query.filter(id_col == model_id, *self.base_filter).update(
            properties
        )
        if is_commit:
            try:
                self.session.flush()
                self.session.commit()
            except SQLAlchemyError as ex:
                self.session.rollback()
                raise ex
        return modify_count

    def update_by_ids(
            self,
            model_ids: List,
            properties: [Dict] = None,
            is_commit=True,
            id_field="id",
    ):
        query = self.session.query(self.model_cls)
        id_col = getattr(self.model_cls, id_field or "id", None)
        modify_count = query.filter(id_col.in_(model_ids), *self.base_filter).update(
            properties, synchronize_session=False
        )
        if is_commit:
            try:
                self.session.flush()
                self.session.commit()
            except SQLAlchemyError as ex:
                self.session.rollback()
                raise ex
        return modify_count

    def delete_obj(self, model: model_cls, commit: bool = True) -> model_cls:
        """
        物理删除
        :param model: model实例对象
        :param commit:
        :return: model实例对象
        """
        try:
            self.session.delete(model)
            if commit:
                self.session.commit()
        except SQLAlchemyError as ex:  # pragma: no cover
            self.session.rollback()
            raise ex
        return model

    def delete_by_id(self, model_id, is_commit=True, id_field: str = "id"):
        """
        物理删除
        :param model_id:
        :param is_commit:
        :param id_field:
        :return:
        """
        query = self.session.query(self.model_cls)
        id_col = getattr(self.model_cls, id_field or "id", None)
        try:
            modify_count = query.filter(
                id_col == model_id,
            ).delete()
            if is_commit:
                self.session.commit()
        except SQLAlchemyError as ex:
            self.session.rollback()
            raise ex
        return modify_count

    def delete_by_ids(self, model_ids: List, is_commit=True, id_field=None):
        """
        批量物理删除
        :param model_ids:
        :param is_commit:
        :param id_field:
        :return:
        """
        query = self.session.query(self.model_cls)
        id_col = getattr(self.model_cls, id_field or "id", None)
        try:
            modify_count = query.filter(id_col.in_(model_ids)).delete(
                synchronize_session=False
            )
            if is_commit:
                self.session.commit()
        except SQLAlchemyError as ex:
            self.session.rollback()
            raise ex
        return modify_count

    def logic_to_delete(
            self,
            model_id: Union[int, str],
            delete_field="is_delete",
            is_commit=True,
            id_field: str = "id",
    ):
        """
        逻辑删除
        :param model_id: ID
        :param delete_field: 逻辑删除字段
        :param is_commit: is_commit
        :param id_field: 查询字段
        :return:
        """
        query = self.session.query(self.model_cls)
        id_col = getattr(self.model_cls, id_field or "id", None)
        try:
            modify_count = query.filter(id_col == model_id, *self.base_filter).update(
                {delete_field: 1}
            )
            if is_commit:
                self.session.commit()
        except SQLAlchemyError as ex:
            self.session.rollback()
            raise ex
        return modify_count

    def logic_to_deletes(
            self,
            model_ids: List,
            delete_field="is_delete",
            is_commit=True,
            id_field: str = "id",
    ):
        """
        批量逻辑删除
        :param model_ids: IDS
        :param delete_field: 逻辑删除字段
        :param is_commit: is_commit
        :param id_field: 查询字段
        :return:
        """
        query = self.session.query(self.model_cls)
        id_col = getattr(self.model_cls, id_field or "id", None)
        try:
            modify_count = query.filter(id_col.in_(list(model_ids)), *self.base_filter).update({delete_field: 1},
                                                                                               synchronize_session=False)
            if is_commit:
                self.session.commit()
        except SQLAlchemyError as ex:
            self.session.rollback()
            raise ex
        return modify_count
