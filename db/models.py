from sqlalchemy import Column, func, DateTime, Integer, String
from sqlalchemy.orm import joinedload, Session

from db.base_model import BaseColumn
from db.conn import Base, db

default_column = BaseColumn
default_column.set_column("id", db.session, id=Column(Integer, primary_key=True, index=True), created_at = Column(DateTime, nullable=False, default=func.utc_timestamp()), updated_at = Column(DateTime, nullable=False, default=func.utc_timestamp(), onupdate=func.utc_timestamp()))


class BaseMixin(default_column):
    def __init__(self, **kwargs):
        self._q = None
        self._session = None
        self.served = None
        self._is_filtered = False
        self._filter_defaults = kwargs

    def all_columns(self):
        return [c for c in self.__table__.columns if c.primary_key is False]

    def all_columns_w_pk(self):
        return [c for c in self.__table__.columns if c.primary_key is False]

    def get_rel_fields(self):
        fields = []
        for _, value in self.__dict__.items():
            if not value.get("prop"):
                continue
            if not value.prop.get("back_populates"):
                continue
            fields.append(value.key)
        return fields

    @classmethod
    def create(cls, session: Session=None, auto_commit=False, **kwargs):
        """
        테이블 데이터 적재 전용 함수
        :param session:
        :param auto_commit: 자동 커밋 여부
        :param kwargs: 적재 할 데이터
        :return:
        """
        obj = cls()
        sess = next(cls.session()) if not session else session
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        sess.add(obj)
        sess.flush()
        if auto_commit:
            sess.commit()
        if not session:
            sess.close()
        return obj

    @classmethod
    def get(cls, session: Session = None, **kwargs):
        """
        Simply get a Row
        :param session:
        :param kwargs:
        :return:
        """
        sess = next(cls.session()) if not session else session
        query = sess.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)

        if query.count() > 1:
            raise Exception("Only one row is supposed to be returned, but got more than one.")
        result = query.first()
        if not session:
            sess.close()
        return result

    @classmethod
    def filter(cls, session: Session = None, **kwargs):
        """
        Simply get a Row
        :param session:
        :param kwargs:
        :return:
        """
        cond = []

        for key, val in kwargs.items():
            key = key.split("__")
            if len(key) > 2:
                col = getattr(cls, key[-2])
            else:
                continue
            if len(key) == 1: cond.append((col == val))
            elif len(key) > 1 and key[-1] == 'gt': cond.append((col > val))
            elif len(key) > 1 and key[-1] == 'gte': cond.append((col >= val))
            elif len(key) > 1 and key[-1] == 'lt': cond.append((col < val))
            elif len(key) > 1 and key[-1] == 'lte': cond.append((col <= val))
            elif len(key) > 1 and key[-1] == 'in': cond.append((col.in_(val)))

        obj = cls()
        if session:
            obj._session = session
            obj.served = True
        else:
            obj._session = next(obj.session())
            obj.served = False
        query = obj._session.query(cls)
        query = query.filter(*cond)
        obj._is_filtered = True
        obj._q = query
        return obj

    @classmethod
    def cls_attr(cls, col_name=None):
        if col_name:
            col = getattr(cls, col_name)
            return col
        else:
            return cls

    def order_by(self, *args: str):
        for a in args:
            if a.startswith("-"):
                col_name = a[1:]
                is_asc = False
            else:
                col_name = a
                is_asc = True
            col = self.cls_attr(col_name)
            self._q = self._q.order_by(col.asc()) if is_asc else self._q.order_by(col.desc())
        return self

    @classmethod
    def prefetch(cls, *args, session: Session = None):
        obj = cls()
        if session:
            obj._session = session
            obj.served = True
        else:
            obj._session = next(obj.session())
            obj.served = False
        query = obj._session.query(cls)
        load_list = []
        for arg in args:
            arg = arg.split("__")
            join = joinedload(arg[0])
            for a in arg[1:]:
                join = join.joinedload(a)
            load_list.append(join)
        query = query.options(*load_list)
        obj._q = query
        return obj
        # (
        #     session.query(schema.Shop)
        #         .options(
        #         joinedload(schema.Shop.google),
        #         joinedload(schema.Shop.facebook)
        #             .joinedload(schema.ShopFacebook.pages)
        #             .joinedload(schema.ShopFacebookPage.instagrams),
        #         joinedload(schema.Shop.hosting),
        #         joinedload(schema.Shop.naver),
        #     )
        #         .filter(schema.Shop.id == shop_id, schema.Shop.business_id == business_id)
        #         .first()
        # )
    def update(self, auto_commit: bool = False, **kwargs):
        if not self._is_filtered:
            raise Exception("Query has no where clauses.")
        qs = self._q.update(kwargs)
        get_id = getattr(self, self.pk)
        ret = None

        self._session.flush()
        if qs > 0:
            ret = self._q.first()
        if auto_commit:
            self._session.commit()
        return ret

    def first(self):
        return self.processor(self._q.first())

    def delete(self, auto_commit: bool = False):
        self.processor(self._q.delete(), auto_commit=auto_commit)

    def all(self):
        return self.processor(self._q.all)

    def count(self):
        return self.processor(self._q.count)

    def processor(self, fun, **kwargs):
        try:
            result = fun()
            auto_commit = kwargs.get("auto_commit", None)
            self._session.commit() if auto_commit else self._session.flush()
        except Exception as e:
            raise e
        finally:
            self.close()
        return result

    def close(self):
        if not self.served:
            self._session.close()
        else:
            self._session.flush()


class Users(Base, BaseMixin):
    __tablename__ = "users"
    email = Column(String(length=100), nullable=True)
    full_name = Column(String(length=100), nullable=True)
