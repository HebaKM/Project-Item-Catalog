from datetime import datetime as dt

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Cuisine(Base):
    __tablename__ = 'cuisine'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref=backref(
        "cuisines", cascade="all,delete"))

    # recipes = relationship('Recipe', backref='cuisine', cascade="all,delete")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Recipe(Base):
    __tablename__ = 'recipe'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    creationDate = Column(DateTime, index=True, default=dt.utcnow)

    cuisine_id = Column(Integer, ForeignKey('cuisine.id'))
    cuisine = relationship(Cuisine, backref=backref(
        "recipes", cascade="all,delete"))

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref=backref(
        "recipes", cascade="all,delete"))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'creationDate': self.creationDate,
        }


engine = create_engine('sqlite:///catalogwithuserdb.db')

Base.metadata.create_all(engine)
