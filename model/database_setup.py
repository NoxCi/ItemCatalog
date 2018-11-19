from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    email = Column(String(256), nullable=False)
    picture = Column(String(256))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture':self.picture
        }

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer,primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    name = Column(String(256),nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id' : self.user_id,
            'name': self.name
        }

class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(Category)
    name = Column(String(256),nullable=False)
    description = Column(String(256))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'category_id' : self.category_id,
            'name': self.name,
            'description': self.description
        }

engine = create_engine('sqlite:///model/catalog.db')


Base.metadata.create_all(engine)
