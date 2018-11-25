import json
from app.models.model_base import Base
from app.models.model_base import ModelBase
from sqlalchemy import Column, Integer, String


class User(Base, ModelBase):

    __tablename__ = 'user'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(50))
    email = Column("email", String(120))

    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return "User(" + json.dumps(self.to_dict()) + ")"
