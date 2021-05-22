from db.conn import Base


class BaseColumn:
    pk = None
    session = None
    tables = []

    @classmethod
    def set_column(cls, pk, session, **kwargs):
        cls.pk = pk
        cls.session = session
        for k, v in kwargs.items():
            setattr(cls, k, v)

    def add_tables(cls, tablename):
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            classname = cls.__name__
            if not classname.startswith('_'):
                tblname = cls.__tablename__
                Base.TBLNAME_TO_CLASS[tblname] = cls

    def __hash__(self):
        return hash(self.pk)
