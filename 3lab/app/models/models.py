from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    charset = Column(String)
    max_length = Column(Integer)
    status = Column(String)
    progress = Column(Integer)
    result = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
